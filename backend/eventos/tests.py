"""Testes do hotsite do evento: programação, item de inscrição na loja e API pública."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from ecommerce.models import CatalogItem
from eventos.models import AtividadeProgramacao, CallForPapers, EventoAcademico, InscricaoEvento
from eventos.views import (
    AtividadeProgramacaoViewSet,
    EventoAcademicoViewSet,
    PublicEventoDetailView,
    PublicEventoListView,
)

factory = APIRequestFactory()


def _evento(**kwargs):
    inicio = timezone.now() + timedelta(days=30)
    dados = dict(
        titulo="Congresso Brasileiro",
        data_inicio=inicio,
        data_fim=inicio + timedelta(days=2),
        status="inscricoes_abertas",
        publicado_site=True,
    )
    dados.update(kwargs)
    return EventoAcademico.objects.create(**dados)


def _publico(view, **kwargs):
    return view.as_view()(factory.get("/?schema=teste"), **kwargs)


@pytest.mark.django_db
class TestItemLoja:
    def _salvar(self, user, evento, data):
        request = factory.post("/", data, format="json")
        force_authenticate(request, user=user)
        return EventoAcademicoViewSet.as_view({"post": "item_loja"})(request, pk=evento.pk)

    def test_cria_e_atualiza_item_de_inscricao(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            evento = _evento()
            resp = self._salvar(board_user, evento, {"price": "200.00", "member_price": "120.00"})
            assert resp.status_code == 200, resp.data
            assert resp.data["item_loja"]["member_price"] == "120.00"

            resp = self._salvar(board_user, evento, {"price": "250.00", "member_price": None})
            assert resp.data["item_loja"]["price"] == "250.00"
            assert resp.data["item_loja"]["member_price"] is None
            assert CatalogItem.objects.filter(evento=evento).count() == 1
            evento.refresh_from_db()
            assert evento.valor_inscricao == Decimal("250.00")

    def test_preco_de_socio_maior_rejeitado(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            resp = self._salvar(board_user, _evento(), {"price": "100.00", "member_price": "150.00"})
            assert resp.status_code == 400


@pytest.mark.django_db
class TestProgramacao:
    def test_fim_antes_do_inicio_rejeitado(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            evento = _evento()
            inicio = evento.data_inicio
            request = factory.post(
                "/",
                {
                    "evento": str(evento.id),
                    "titulo": "Abertura",
                    "inicio": inicio.isoformat(),
                    "fim": (inicio - timedelta(hours=1)).isoformat(),
                },
                format="json",
            )
            force_authenticate(request, user=board_user)
            resp = AtividadeProgramacaoViewSet.as_view({"post": "create"})(request)
            assert resp.status_code == 400
            assert "fim" in resp.data

    def test_associado_nao_edita(self, test_tenant, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            request = factory.get("/")
            force_authenticate(request, user=user)
            assert AtividadeProgramacaoViewSet.as_view({"get": "list"})(request).status_code == 403


@pytest.mark.django_db
class TestHotsitePublico:
    def test_lista_so_publicados(self, test_tenant):
        with schema_context(test_tenant.schema_name):
            _evento(titulo="Publicado", slug="publicado")
            _evento(titulo="Interno", slug="interno", publicado_site=False)
            _evento(titulo="Rascunho", slug="rascunho", status="rascunho")
        resp = _publico(PublicEventoListView)
        assert resp.status_code == 200
        assert [e["slug"] for e in resp.data] == ["publicado"]

    def test_detalhe_com_programacao_chamada_e_inscricao(self, test_tenant):
        with schema_context(test_tenant.schema_name):
            evento = _evento(slug="cbx", capacidade_max=2)
            AtividadeProgramacao.objects.create(
                evento=evento,
                titulo="Conferência de abertura",
                inicio=evento.data_inicio,
                fim=evento.data_inicio + timedelta(hours=1),
                sala="Auditório",
            )
            CallForPapers.objects.create(
                evento=evento,
                titulo="Chamada de trabalhos",
                instrucoes="Resumo de até 500 palavras.",
                data_abertura=timezone.now() - timedelta(days=1),
                data_fechamento=timezone.now() + timedelta(days=10),
                areas_tematicas=["Ensino", "Pesquisa"],
            )
            CatalogItem.objects.create(
                name="Inscrição", item_type="inscricao", evento=evento,
                price=Decimal("200.00"), member_price=Decimal("120.00"),
            )
            InscricaoEvento.objects.create(evento=evento, nome="A", email="a@x.org", confirmada=True)

        resp = _publico(PublicEventoDetailView, slug="cbx")
        assert resp.status_code == 200, resp.data
        assert resp.data["programacao"][0]["sala"] == "Auditório"
        assert resp.data["chamada"]["aberta"] is True
        assert resp.data["chamada"]["areas_tematicas"] == ["Ensino", "Pesquisa"]
        inscricao = resp.data["inscricao"]
        assert inscricao["aberta"] is True
        assert inscricao["vagas_restantes"] == 1
        assert inscricao["member_price"] == "120.00"

    def test_esgotado_fecha_inscricao(self, test_tenant):
        with schema_context(test_tenant.schema_name):
            evento = _evento(slug="lotado", capacidade_max=1)
            CatalogItem.objects.create(name="Inscrição", item_type="inscricao", evento=evento, price=Decimal("10"))
            InscricaoEvento.objects.create(evento=evento, nome="A", email="a@x.org", confirmada=True)
        inscricao = _publico(PublicEventoDetailView, slug="lotado").data["inscricao"]
        assert inscricao["aberta"] is False
        assert inscricao["esgotada"] is True

    def test_nao_publicado_404(self, test_tenant):
        with schema_context(test_tenant.schema_name):
            _evento(slug="oculto", publicado_site=False)
        assert _publico(PublicEventoDetailView, slug="oculto").status_code == 404
