"""Testes do preço de sócio adimplente na loja."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from ecommerce.models import CatalogItem, CatalogItemType, OrderItem
from ecommerce.views import CartViewSet, CatalogItemViewSet
from membros.models import Anuidade, AnuidadeStatus, Filiacao, FiliacaoStatus
from membros.services import membro_adimplente

factory = APIRequestFactory()


def _call(viewset, actions, method, user, data=None):
    request = getattr(factory, method)("/", data or {}, format="json")
    force_authenticate(request, user=user)
    return viewset.as_view(actions)(request)


def _filiar(membro, status=FiliacaoStatus.ATIVA):
    return Filiacao.objects.create(membro=membro, data_inicio=date(2025, 1, 1), status=status)


def _material(**kwargs):
    defaults = dict(
        name="Livro de resumos",
        item_type=CatalogItemType.DIGITAL,
        price=Decimal("100.00"),
        member_price=Decimal("60.00"),
    )
    defaults.update(kwargs)
    return CatalogItem.objects.create(**defaults)


@pytest.mark.django_db
class TestMembroAdimplente:
    def test_regras(self, test_tenant, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            assert not membro_adimplente(membro)
            assert not membro_adimplente(None)

            filiacao = _filiar(membro)
            assert membro_adimplente(membro)

            # Atrasada mesmo antes do cron marcar como vencida
            anuidade = Anuidade.objects.create(
                filiacao=filiacao,
                ano_referencia=2026,
                valor=Decimal("80.00"),
                vencimento=date.today() - timedelta(days=1),
                status=AnuidadeStatus.PENDENTE,
            )
            assert not membro_adimplente(membro)

            anuidade.status = AnuidadeStatus.PAGA
            anuidade.save()
            assert membro_adimplente(membro)

            filiacao.status = FiliacaoStatus.INADIMPLENTE
            filiacao.save()
            assert not membro_adimplente(membro)

    def test_honorario_e_adimplente(self, test_tenant, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            _filiar(membro, FiliacaoStatus.HONORARIA)
            assert membro_adimplente(membro)


@pytest.mark.django_db
class TestPrecoSocio:
    def test_adimplente_paga_preco_de_socio(self, test_tenant, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            _filiar(membro)
            item = _material()

            loja = _call(CatalogItemViewSet, {"get": "loja"}, "get", user)
            assert loja.data[0]["preco_final"] == "60.00"

            cart = _call(CartViewSet, {"post": "add_item"}, "post", user, {"catalog_item": str(item.id)})
            assert cart.status_code == 200, cart.data
            assert cart.data["adimplente"] is True
            assert cart.data["total"] == "60.00"
            assert cart.data["total_cheio"] == "100.00"

            order = _call(CartViewSet, {"post": "checkout"}, "post", user, {"payment_method": "manual"})
            assert order.status_code == 201, order.data
            assert order.data["total_amount"] == "60.00"
            linha = OrderItem.objects.get(order_id=order.data["id"])
            assert linha.price_at_purchase == Decimal("60.00")
            assert linha.list_price == Decimal("100.00")

    def test_inadimplente_paga_preco_cheio(self, test_tenant, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            _filiar(membro, FiliacaoStatus.INADIMPLENTE)
            item = _material()

            loja = _call(CatalogItemViewSet, {"get": "loja"}, "get", user)
            assert loja.data[0]["preco_final"] == "100.00"
            assert loja.data[0]["member_price"] == "60.00"

            cart = _call(CartViewSet, {"post": "add_item"}, "post", user, {"catalog_item": str(item.id)})
            assert cart.data["adimplente"] is False
            assert cart.data["total"] == "100.00"

            order = _call(CartViewSet, {"post": "checkout"}, "post", user, {"payment_method": "manual"})
            assert order.data["total_amount"] == "100.00"

    def test_sem_preco_de_socio_cobra_igual(self, test_tenant, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            _filiar(membro)
            _material(member_price=None)
            loja = _call(CatalogItemViewSet, {"get": "loja"}, "get", user)
            assert loja.data[0]["preco_final"] == "100.00"

    def test_diretoria_nao_recebe_preco_final(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            _material()
            resp = _call(CatalogItemViewSet, {"get": "list"}, "get", board_user)
            itens = resp.data["results"] if isinstance(resp.data, dict) else resp.data
            assert itens[0]["preco_final"] is None


@pytest.mark.django_db
class TestValidacaoPrecoSocio:
    def _criar(self, user, **data):
        payload = {"name": "Item", "item_type": "digital", "price": "100.00", **data}
        return _call(CatalogItemViewSet, {"post": "create"}, "post", user, payload)

    def test_maior_que_cheio_rejeitado(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            resp = self._criar(board_user, member_price="120.00")
            assert resp.status_code == 400
            assert "member_price" in resp.data

    def test_anuidade_nao_aceita(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            resp = self._criar(board_user, item_type="anuidade", anuidade_ano=2026, member_price="50.00")
            assert resp.status_code == 400

    def test_valido(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            resp = self._criar(board_user, member_price="70.00")
            assert resp.status_code == 201, resp.data
            assert resp.data["member_price"] == "70.00"


@pytest.mark.django_db
class TestCheckoutSimulado:
    def _checkout(self, user, membro):
        _filiar(membro)
        _material()
        item = CatalogItem.objects.get()
        _call(CartViewSet, {"post": "add_item"}, "post", user, {"catalog_item": str(item.id)})
        return _call(CartViewSet, {"post": "checkout"}, "post", user, {"payment_method": "simulated"})

    def test_bloqueado_fora_da_demo(self, test_tenant, member, settings):
        settings.PAGAMENTO_SIMULADO = False
        user, membro = member
        with schema_context(test_tenant.schema_name):
            assert self._checkout(user, membro).status_code == 400

    def test_liberado_na_demo(self, test_tenant, member, settings):
        settings.PAGAMENTO_SIMULADO = True
        user, membro = member
        with schema_context(test_tenant.schema_name):
            resp = self._checkout(user, membro)
            assert resp.status_code == 201
            assert resp.data["status"] == "fulfilled"
