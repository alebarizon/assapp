"""Testes da carteirinha digital: situação, validade, QR, PDF e verificação pública."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from membros.carteirinha import situacao
from membros.models import Anuidade, Filiacao, Membro
from membros.views import (
    MembroViewSet,
    MinhaCarteirinhaPdfView,
    MinhaCarteirinhaView,
    VerificarCarteirinhaView,
)

factory = APIRequestFactory()


def _get(user):
    request = factory.get("/")
    force_authenticate(request, user=user)
    return request


def _filiar(membro, status="ativa", tipo="efetivo"):
    return Filiacao.objects.create(membro=membro, status=status, tipo=tipo, data_inicio=date(2024, 3, 1))


def _anuidade(filiacao, ano, status, vencimento):
    return Anuidade.objects.create(
        filiacao=filiacao, ano_referencia=ano, valor=Decimal("200"), vencimento=vencimento, status=status
    )


@pytest.mark.django_db
class TestSituacao:
    def test_em_dia_vale_ate_fim_do_ano_pago(self, test_tenant, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            f = _filiar(membro)
            _anuidade(f, 2026, "paga", date(2026, 3, 31))
            s = situacao(membro, hoje=date(2026, 10, 18))
        assert s["situacao"] == "em_dia"
        assert s["valida_ate"] == date(2026, 12, 31)
        assert s["tipo"] == "Efetivo"
        assert s["membro_desde"] == date(2024, 3, 1)

    def test_pendente_quando_anuidade_atrasada(self, test_tenant, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            f = _filiar(membro)
            _anuidade(f, 2026, "pendente", timezone.localdate() - timedelta(days=5))
            s = situacao(membro)
        assert s["situacao"] == "pendente"
        assert s["valida_ate"] is None

    def test_anuidade_a_vencer_mantem_em_dia(self, test_tenant, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            f = _filiar(membro)
            vence = timezone.localdate() + timedelta(days=20)
            _anuidade(f, vence.year, "pendente", vence)
            s = situacao(membro)
        assert s["situacao"] == "em_dia"
        assert s["valida_ate"] == vence

    def test_honorario_e_inativo(self, test_tenant, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            f = _filiar(membro, status="honoraria", tipo="honorario")
            honorario = situacao(membro)
            f.status = "cancelada"
            f.save()
            cancelado = situacao(membro)
        assert honorario["situacao"] == "em_dia" and honorario["honoraria"] is True
        assert cancelado["situacao"] == "inativo"


@pytest.mark.django_db
class TestEndpoints:
    def test_minha_carteirinha_qr_e_pdf(self, test_tenant, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            _filiar(membro)
            outro = Membro.objects.create(nome_completo="Beto", email="beto@x.org", matricula=41)
            resp = MinhaCarteirinhaView.as_view()(_get(user))
            assert resp.status_code == 200
            assert resp.data["matricula"] == "000042"
            assert resp.data["qr"].startswith("data:image/svg+xml;base64,")
            assert f"/site/carteirinha/{resp.data['codigo']}?schema=teste" in resp.data["url_verificacao"]
            assert "cpf" not in resp.data and "email" not in resp.data

            again = MinhaCarteirinhaView.as_view()(_get(user))
            assert again.data["codigo"] == resp.data["codigo"]
            assert outro.matricula == 41

            pdf = MinhaCarteirinhaPdfView.as_view()(_get(user))
            assert pdf.status_code == 200
            assert pdf.content.startswith(b"%PDF")

    def test_usuario_sem_membro(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            resp = MinhaCarteirinhaView.as_view()(_get(board_user))
        assert resp.status_code == 404

    def test_verificacao_publica_e_renovacao(self, test_tenant, member, board_user):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            _filiar(membro)
            codigo = MinhaCarteirinhaView.as_view()(_get(user)).data["codigo"]

        ok = VerificarCarteirinhaView.as_view()(factory.get("/?schema=teste"), codigo=codigo)
        assert ok.status_code == 200
        assert ok.data["nome"] == "Ana Maria Silva"
        assert ok.data["situacao"] == "em_dia"
        assert "email" not in ok.data

        with schema_context(test_tenant.schema_name):
            request = factory.post("/")
            force_authenticate(request, user=board_user)
            novo = MembroViewSet.as_view({"post": "carteirinha_renovar"})(request, pk=membro.pk)
            assert novo.status_code == 200
            assert novo.data["codigo"] != codigo

        antigo = VerificarCarteirinhaView.as_view()(factory.get("/?schema=teste"), codigo=codigo)
        assert antigo.status_code == 404
