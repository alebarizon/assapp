"""Testes da régua de anuidades e da linha do tempo do associado."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail
from django.core.management import call_command
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from membros.models import Anuidade, AnuidadeStatus, Filiacao, LembreteAnuidade
from membros.services import enviar_lembretes_anuidade, etapa_devida, registrar_pagamento
from membros.views import AnuidadeViewSet, MembroViewSet

factory = APIRequestFactory()
HOJE = date(2026, 3, 1)


@pytest.fixture(autouse=True)
def _email_em_memoria(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


def _anuidade(membro, vencimento, status=AnuidadeStatus.PENDENTE, valor="80.00", ano=2026):
    filiacao = membro.filiacoes.first() or Filiacao.objects.create(membro=membro, data_inicio=date(2025, 1, 1))
    return Anuidade.objects.create(
        filiacao=filiacao, ano_referencia=ano, valor=Decimal(valor), vencimento=vencimento, status=status
    )


class TestEtapaDevida:
    @pytest.mark.parametrize(
        "dias_ate_vencimento,esperada",
        [
            (40, None),
            (30, LembreteAnuidade.ANTES_30),
            (20, LembreteAnuidade.ANTES_30),
            (15, LembreteAnuidade.ANTES_15),
            (0, LembreteAnuidade.NO_DIA),
            (-14, LembreteAnuidade.NO_DIA),
            (-15, LembreteAnuidade.DEPOIS_15),
        ],
    )
    def test_etapa(self, dias_ate_vencimento, esperada):
        anuidade = Anuidade(vencimento=HOJE + timedelta(days=dias_ate_vencimento))
        assert etapa_devida(anuidade, HOJE) == esperada


@pytest.mark.django_db
class TestRegua:
    def test_envia_etapa_devida_uma_unica_vez(self, test_tenant, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            anuidade = _anuidade(membro, HOJE + timedelta(days=15))

            resultado = enviar_lembretes_anuidade(hoje=HOJE)
            assert resultado["enviados"] == 1
            assert resultado["por_etapa"][LembreteAnuidade.ANTES_15] == 1
            assert len(mail.outbox) == 1
            assert mail.outbox[0].to == ["ana@teste.org"]
            assert "/app/portal/perfil" in mail.outbox[0].body

            assert enviar_lembretes_anuidade(hoje=HOJE)["enviados"] == 0
            assert LembreteAnuidade.objects.filter(anuidade=anuidade).count() == 1

    def test_pula_etapas_anteriores_ja_ultrapassadas(self, test_tenant, member):
        """Lote gerado tarde: só a etapa atual é enviada, não as anteriores."""
        _, membro = member
        with schema_context(test_tenant.schema_name):
            anuidade = _anuidade(membro, HOJE)
            enviar_lembretes_anuidade(hoje=HOJE)
            assert list(anuidade.lembretes.values_list("etapa", flat=True)) == [LembreteAnuidade.NO_DIA]

            # Uma etapa anterior nunca é enviada depois de uma posterior
            enviar_lembretes_anuidade(hoje=HOJE)
            assert anuidade.lembretes.count() == 1

            enviar_lembretes_anuidade(hoje=HOJE + timedelta(days=15))
            assert set(anuidade.lembretes.values_list("etapa", flat=True)) == {
                LembreteAnuidade.NO_DIA,
                LembreteAnuidade.DEPOIS_15,
            }

    def test_ignora_paga_isenta_antiga_e_inativo(self, test_tenant, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            _anuidade(membro, HOJE, status=AnuidadeStatus.PAGA, ano=2026)
            _anuidade(membro, HOJE, status=AnuidadeStatus.PENDENTE, valor="0.00", ano=2025)
            _anuidade(membro, HOJE - timedelta(days=120), status=AnuidadeStatus.VENCIDA, ano=2024)
            assert enviar_lembretes_anuidade(hoje=HOJE)["enviados"] == 0

            membro.ativo = False
            membro.save()
            _anuidade(membro, HOJE, ano=2027)
            assert enviar_lembretes_anuidade(hoje=HOJE)["enviados"] == 0

    def test_falha_de_email_nao_registra_e_tenta_de_novo(self, test_tenant, member, monkeypatch):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            anuidade = _anuidade(membro, HOJE)
            monkeypatch.setattr("core.emails.enviar_email", lambda *a, **k: False)
            resultado = enviar_lembretes_anuidade(hoje=HOJE)
            assert resultado == {**resultado, "enviados": 0, "falhas": 1}
            assert not anuidade.lembretes.exists()

    def test_endpoint_diretoria(self, test_tenant, board_user, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            _anuidade(membro, date.today())
            request = factory.post("/", {}, format="json")
            force_authenticate(request, user=board_user)
            resp = AnuidadeViewSet.as_view({"post": "enviar_lembretes"})(request)
            assert resp.status_code == 200, resp.data
            assert resp.data["enviados"] == 1

    def test_endpoint_bloqueia_associado(self, test_tenant, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            request = factory.post("/", {}, format="json")
            force_authenticate(request, user=user)
            resp = AnuidadeViewSet.as_view({"post": "enviar_lembretes"})(request)
            assert resp.status_code == 403

    def test_comando_roda_por_schema(self, test_tenant, member, capsys):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            _anuidade(membro, date.today() - timedelta(days=1))
        call_command("regua_anuidades", schema=test_tenant.schema_name)
        saida = capsys.readouterr().out
        assert "[teste] vencidas=1 inadimplentes=1 lembretes=1 falhas=0" in saida
        with schema_context(test_tenant.schema_name):
            assert Anuidade.objects.get().status == AnuidadeStatus.VENCIDA


@pytest.mark.django_db
class TestTimeline:
    def test_agrega_eventos_do_associado(self, test_tenant, board_user, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            anuidade = _anuidade(membro, HOJE)
            LembreteAnuidade.objects.create(anuidade=anuidade, etapa=LembreteAnuidade.NO_DIA, email=membro.email)
            registrar_pagamento(anuidade)

            request = factory.get("/")
            force_authenticate(request, user=board_user)
            resp = MembroViewSet.as_view({"get": "timeline"})(request, pk=membro.pk)
            assert resp.status_code == 200, resp.data
            categorias = [item["categoria"] for item in resp.data]
            assert categorias[:2] == ["anuidade", "lembrete"]
            assert "filiacao" in categorias
            assert resp.data[0]["titulo"] == "Anuidade 2026 paga"

    def test_registrar_pagamento_idempotente(self, test_tenant, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            anuidade = registrar_pagamento(_anuidade(membro, HOJE))
            pago_em = anuidade.pago_em
            assert registrar_pagamento(anuidade).pago_em == pago_em
