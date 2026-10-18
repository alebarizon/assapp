"""Publicações: cadastro com item na loja, paywall por adimplência e compra."""
from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from ecommerce.models import CartItem
from ecommerce.services import create_order_from_cart, get_or_create_cart, process_order_payment, validate_cart_item_for_membro
from membros.models import Filiacao, FiliacaoStatus
from publicacoes.models import Publicacao
from publicacoes.views import (
    MinhaPublicacaoArquivoView,
    MinhasPublicacoesView,
    PublicacaoViewSet,
    PublicPublicacaoArquivoView,
    PublicPublicacaoListView,
)

factory = APIRequestFactory()


def _criar(user, **dados):
    payload = {"titulo": "Dossiê Clima", "tipo": "dossie", "publicada": True, **dados}
    request = factory.post("/", payload, format="multipart")
    force_authenticate(request, user=user)
    return PublicacaoViewSet.as_view({"post": "create"})(request)


def _pdf():
    return SimpleUploadedFile("dossie.pdf", b"%PDF-1.4 teste", content_type="application/pdf")


def _minhas(user):
    request = factory.get("/")
    force_authenticate(request, user=user)
    return MinhasPublicacoesView.as_view()(request)


def _baixar(user, pub):
    request = factory.get("/")
    force_authenticate(request, user=user)
    return MinhaPublicacaoArquivoView.as_view()(request, pk=pub.pk)


@pytest.mark.django_db
class TestPublicacoes:
    def test_venda_cria_item_digital_na_loja(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            resp = _criar(board_user, acesso="venda", preco="40.00", preco_socio="25.00", arquivo=_pdf())
            assert resp.status_code == 201, resp.data
            pub = Publicacao.objects.get()
            assert pub.publicado_em and pub.catalog_item.item_type == "digital"
            assert pub.catalog_item.is_active and str(pub.catalog_item.member_price) == "25.00"
            assert resp.data["preco"] == "40.00"

            sem_preco = _criar(board_user, titulo="Outro", acesso="venda", preco="", ano="")
            assert sem_preco.status_code == 400 and "preco" in sem_preco.data

            aberto = _criar(board_user, titulo="Aberto", acesso="associados", preco="", preco_socio="", ano="")
            assert aberto.status_code == 201, aberto.data
            assert aberto.data["preco"] is None and aberto.data["ano"] is None

    def test_paywall_associados(self, test_tenant, board_user, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            _criar(board_user, acesso="associados", arquivo=_pdf())
            pub = Publicacao.objects.get()

            item = _minhas(user).data[0]
            assert item["liberado"] is False and item["motivo"] == "requer_adimplencia"
            assert _baixar(user, pub).status_code == 403

            Filiacao.objects.create(membro=membro, data_inicio=date(2025, 1, 1), status=FiliacaoStatus.ATIVA)
            assert _minhas(user).data[0]["motivo"] == "adimplente"
            assert _baixar(user, pub).status_code == 200
            pub.refresh_from_db()
            assert pub.downloads == 1

    def test_compra_libera_e_bloqueia_recompra(self, test_tenant, board_user, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            _criar(board_user, acesso="venda", preco="40.00", arquivo=_pdf())
            pub = Publicacao.objects.get()
            item = _minhas(user).data[0]
            assert item["motivo"] == "requer_compra" and item["catalog_item"] == str(pub.catalog_item_id)
            assert item["preco_final"] == "40.00"

            cart = get_or_create_cart(membro)
            CartItem.objects.create(cart=cart, catalog_item=pub.catalog_item)
            order = create_order_from_cart(membro, user=user)
            process_order_payment(order, user=user)

            item = _minhas(user).data[0]
            assert item["motivo"] == "comprado" and item["catalog_item"] is None
            assert _baixar(user, pub).status_code == 200
            with pytest.raises(ValidationError):
                validate_cart_item_for_membro(pub.catalog_item, membro, 1)

    def test_site_publico(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            _criar(board_user, titulo="Boletim 1", tipo="boletim", acesso="publico", arquivo=_pdf())
            _criar(board_user, titulo="Restrito", acesso="associados", arquivo=_pdf())
            _criar(board_user, titulo="Rascunho", acesso="publico", publicada=False)
            aberto = Publicacao.objects.get(titulo="Boletim 1")
            restrito = Publicacao.objects.get(titulo="Restrito")

        lista = PublicPublicacaoListView.as_view()(factory.get("/?schema=teste"))
        assert {p["titulo"] for p in lista.data} == {"Boletim 1", "Restrito"}
        view = PublicPublicacaoArquivoView.as_view()
        assert view(factory.get("/?schema=teste"), slug=aberto.slug).status_code == 200
        assert view(factory.get("/?schema=teste"), slug=restrito.slug).status_code == 403

    def test_mudar_para_aberto_tira_da_loja(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            _criar(board_user, acesso="venda", preco="10.00")
            pub = Publicacao.objects.get()
            request = factory.patch("/", {"acesso": "publico"}, format="json")
            force_authenticate(request, user=board_user)
            resp = PublicacaoViewSet.as_view({"patch": "partial_update"})(request, pk=str(pub.pk))
            assert resp.status_code == 200, resp.data
            pub.refresh_from_db()
            assert pub.catalog_item.is_active is False
            assert resp.data["preco"] is None

    def test_associado_nao_gerencia(self, test_tenant, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            assert _criar(user).status_code == 403
