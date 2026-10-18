"""Ficha 360 do contato."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from contatos.models import Contato
from contatos.views import ContatoViewSet
from eventos.models import EventoAcademico, InscricaoEvento
from formularios.models import Formulario, Resposta
from membros.models import Anuidade, Filiacao

factory = APIRequestFactory()


def _ficha(user, contato):
    request = factory.get("/")
    force_authenticate(request, user=user)
    return ContatoViewSet.as_view({"get": "ficha"})(request, pk=str(contato.pk))


def _evento():
    agora = timezone.now()
    return EventoAcademico.objects.create(
        titulo="Congresso", slug="congresso", data_inicio=agora, data_fim=agora + timedelta(days=1)
    )


@pytest.mark.django_db
class TestFicha:
    def test_nao_associado_pelo_email(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            contato = Contato.objects.create(nome="Bia", email="bia@x.org", assunto="filiacao")
            Contato.objects.create(nome="Bia Lima", email="BIA@x.org", assunto="eventos")
            InscricaoEvento.objects.create(evento=_evento(), nome="Bia", email="bia@x.org")
            form = Formulario.objects.create(titulo="Pesquisa")
            Resposta.objects.create(formulario=form, email="bia@x.org", enviada_em=timezone.now())
            Resposta.objects.create(formulario=form, email="outra@x.org", enviada_em=timezone.now())

            resp = _ficha(board_user, contato)
        assert resp.status_code == 200
        r = resp.data["resumo"]
        assert r["associado"] is None
        assert r["contatos"] == 2 and r["eventos"] == 1
        titulos = [i["titulo"] for i in resp.data["itens"]]
        assert "Inscrição em Congresso" in titulos
        assert titulos.count("Formulário respondido") == 1
        assert sum(1 for i in resp.data["itens"] if i["categoria"] == "contato") == 2

    def test_associado_vinculado_traz_timeline_e_situacao(self, test_tenant, board_user, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            f = Filiacao.objects.create(membro=membro, status="ativa", data_inicio=date(2024, 1, 1))
            Anuidade.objects.create(
                filiacao=f, ano_referencia=2026, valor=Decimal("150"), vencimento=date(2026, 3, 1),
                status="paga", pago_em=timezone.now(),
            )
            contato = Contato.objects.create(nome="Ana", email="ana@teste.org", membro=membro)
            resp = _ficha(board_user, contato)
        r = resp.data["resumo"]
        assert r["associado"]["id"] == str(membro.id)
        assert r["associado"]["situacao"] == "em_dia"
        titulos = [i["titulo"] for i in resp.data["itens"]]
        assert "Anuidade 2026 paga" in titulos
        assert sum(1 for i in resp.data["itens"] if i["categoria"] == "contato") == 1

    def test_sugere_associado_com_mesmo_email(self, test_tenant, board_user, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            contato = Contato.objects.create(nome="Ana", email="ANA@teste.org")
            resp = _ficha(board_user, contato)
        assert resp.data["resumo"]["associado_mesmo_email"] == {"id": str(membro.id), "nome": membro.nome_completo}

    def test_associado_comum_sem_acesso(self, test_tenant, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            contato = Contato.objects.create(nome="X", email="x@x.org")
            resp = _ficha(user, contato)
        assert resp.status_code == 403
