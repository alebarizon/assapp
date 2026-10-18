"""Testes do pagamento online de anuidades."""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from finance.models import Transaction
from membros.models import Anuidade, AnuidadeStatus, Filiacao, FiliacaoStatus
from payments.gateways import AsaasGateway, GatewayError
from payments.models import Cobranca, ConfiguracaoPagamento
from payments.views import (
    CobrarAnuidadeView,
    ConfiguracaoPagamentoView,
    DisponibilidadeView,
    SimularPagamentoView,
    WebhookAsaasView,
)

factory = APIRequestFactory()


def _post(view, user, data=None, **kwargs):
    request = factory.post("/", data or {}, format="json")
    force_authenticate(request, user=user)
    return view.as_view()(request, **kwargs)


def _anuidade(membro, status=AnuidadeStatus.VENCIDA):
    filiacao = Filiacao.objects.create(
        membro=membro, data_inicio=date(2025, 1, 1), status=FiliacaoStatus.INADIMPLENTE
    )
    return Anuidade.objects.create(
        filiacao=filiacao,
        ano_referencia=2026,
        valor=Decimal("80.00"),
        vencimento=date.today() - timedelta(days=3),
        status=status,
    )


@pytest.fixture
def simulado(settings):
    settings.PAGAMENTO_SIMULADO = True


@pytest.fixture
def sem_simulado(settings):
    settings.PAGAMENTO_SIMULADO = False


@pytest.mark.django_db
class TestFluxoSimulado:
    def test_pix_simulado_quita_anuidade_e_espelha_financeiro(self, test_tenant, member, simulado):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            anuidade = _anuidade(membro)

            resp = _post(CobrarAnuidadeView, user, {"metodo": "pix"}, anuidade_id=anuidade.id)
            assert resp.status_code == 201, resp.data
            assert resp.data["provedor"] == "simulado"
            assert resp.data["pix_copia_cola"]

            # Gerar de novo reaproveita a cobrança em aberto
            resp2 = _post(CobrarAnuidadeView, user, {"metodo": "pix"}, anuidade_id=anuidade.id)
            assert resp2.data["id"] == resp.data["id"]

            cartao = _post(CobrarAnuidadeView, user, {"metodo": "cartao"}, anuidade_id=anuidade.id)
            assert cartao.status_code == 201

            pago = _post(SimularPagamentoView, user, cobranca_id=resp.data["id"])
            assert pago.status_code == 200, pago.data
            assert pago.data["status"] == "paga"

            anuidade.refresh_from_db()
            assert anuidade.status == AnuidadeStatus.PAGA
            assert anuidade.filiacao.status == FiliacaoStatus.ATIVA
            assert Transaction.objects.filter(referencia=f"anuidade:{anuidade.id}").exists()
            assert Cobranca.objects.get(pk=cartao.data["id"]).status == Cobranca.CANCELADA

    def test_nao_cobra_anuidade_de_outro_associado(self, test_tenant, member, board_user, simulado):
        from membros.models import Membro

        user, _ = member
        with schema_context(test_tenant.schema_name):
            outro = Membro.objects.create(nome_completo="Bruno", email="bruno@teste.org")
            anuidade = _anuidade(outro)
            resp = _post(CobrarAnuidadeView, user, {"metodo": "pix"}, anuidade_id=anuidade.id)
            assert resp.status_code == 404

    def test_nao_cobra_anuidade_paga(self, test_tenant, member, simulado):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            anuidade = _anuidade(membro, status=AnuidadeStatus.PAGA)
            resp = _post(CobrarAnuidadeView, user, {"metodo": "pix"}, anuidade_id=anuidade.id)
            assert resp.status_code == 400

    def test_sem_gateway_nem_simulado_fica_indisponivel(self, test_tenant, member, sem_simulado):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            request = factory.get("/")
            force_authenticate(request, user=user)
            assert DisponibilidadeView.as_view()(request).data["habilitado"] is False

            anuidade = _anuidade(membro)
            resp = _post(CobrarAnuidadeView, user, {"metodo": "pix"}, anuidade_id=anuidade.id)
            assert resp.status_code == 400
            assert "não está habilitado" in resp.data["detail"]


@pytest.mark.django_db
class TestConfiguracao:
    def test_chave_cifrada_e_nao_devolvida(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            request = factory.put(
                "/", {"api_key": "$aact_chave_secreta_1234", "ativo": True, "sandbox": True}, format="json"
            )
            force_authenticate(request, user=board_user)
            resp = ConfiguracaoPagamentoView.as_view()(request)
            assert resp.status_code == 200, resp.data
            assert "api_key" not in resp.data
            assert resp.data["api_key_final"] == "…1234"
            assert "schema=teste" in resp.data["webhook_url"]

            config = ConfiguracaoPagamento.atual()
            assert "chave_secreta" not in config.api_key_cifrada
            assert config.api_key == "$aact_chave_secreta_1234"

    def test_ativar_sem_chave_falha(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            request = factory.put("/", {"ativo": True}, format="json")
            force_authenticate(request, user=board_user)
            assert ConfiguracaoPagamentoView.as_view()(request).status_code == 400

    def test_associado_nao_acessa(self, test_tenant, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            request = factory.get("/")
            force_authenticate(request, user=user)
            assert ConfiguracaoPagamentoView.as_view()(request).status_code == 403


@pytest.mark.django_db
class TestWebhook:
    def _cobranca(self, membro, anuidade):
        return Cobranca.objects.create(
            membro=membro,
            anuidade=anuidade,
            descricao="Anuidade 2026",
            valor=anuidade.valor,
            metodo=Cobranca.PIX,
            provedor=ConfiguracaoPagamento.ASAAS,
            external_id="pay_123",
            vencimento=anuidade.vencimento,
        )

    def _webhook(self, payload, token):
        request = factory.post(
            "/?schema=teste", payload, format="json", HTTP_ASAAS_ACCESS_TOKEN=token
        )
        return WebhookAsaasView.as_view()(request)

    def test_pagamento_recebido_quita(self, test_tenant, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            anuidade = _anuidade(membro)
            cobranca = self._cobranca(membro, anuidade)
            token = ConfiguracaoPagamento.atual().webhook_token

        payload = {"event": "PAYMENT_RECEIVED", "payment": {"id": "pay_123"}}
        resp = self._webhook(payload, token)
        assert resp.status_code == 200, resp.data
        assert resp.data["resultado"] == "pago"
        # Reentrega do mesmo evento não duplica nada
        assert self._webhook(payload, token).data["resultado"] == "pago"

        with schema_context(test_tenant.schema_name):
            cobranca.refresh_from_db()
            anuidade.refresh_from_db()
            assert cobranca.status == Cobranca.PAGA
            assert anuidade.status == AnuidadeStatus.PAGA
            assert anuidade.stripe_payment_id == "pay_123"
            assert Transaction.objects.filter(referencia=f"anuidade:{anuidade.id}").count() == 1

    def test_token_invalido(self, test_tenant, member):
        with schema_context(test_tenant.schema_name):
            ConfiguracaoPagamento.atual()
        resp = self._webhook({"event": "PAYMENT_RECEIVED", "payment": {"id": "x"}}, "errado")
        assert resp.status_code == 403

    def test_evento_desconhecido_e_ignorado(self, test_tenant):
        with schema_context(test_tenant.schema_name):
            token = ConfiguracaoPagamento.atual().webhook_token
        resp = self._webhook({"event": "PAYMENT_RECEIVED", "payment": {"id": "nao_existe"}}, token)
        assert resp.data["resultado"] == "desconhecido"


class TestAsaasGateway:
    def _resposta(self, status_code, json_data):
        resp = MagicMock(status_code=status_code)
        resp.json.return_value = json_data
        return resp

    def test_cria_cliente_e_cobranca_pix(self, monkeypatch):
        chamadas = []
        respostas = iter(
            [
                self._resposta(200, {"data": []}),
                self._resposta(200, {"id": "cus_1"}),
                self._resposta(200, {"id": "pay_1", "invoiceUrl": "https://asaas/i/pay_1"}),
                self._resposta(200, {"payload": "000201PIX", "encodedImage": "iVBOR"}),
            ]
        )

        def fake_request(method, url, **kwargs):
            chamadas.append((method, url, kwargs.get("json"), kwargs["headers"]["access_token"]))
            return next(respostas)

        monkeypatch.setattr("payments.gateways.requests.request", fake_request)
        membro = MagicMock(id="m1", nome_completo="Ana", email="ana@x.org", cpf="123.456.789-09", cnpj=None, telefone="")
        cobranca = MagicMock(id="c1", metodo="pix", valor=Decimal("80.00"), vencimento=date(2020, 1, 1), descricao="Anuidade 2026")

        resultado = AsaasGateway("chave", sandbox=True).criar_cobranca(cobranca, membro)

        assert resultado.external_id == "pay_1"
        assert resultado.pix_copia_cola == "000201PIX"
        assert resultado.url_pagamento == "https://asaas/i/pay_1"
        assert chamadas[1][2]["cpfCnpj"] == "12345678909"
        assert chamadas[2][2]["billingType"] == "PIX"
        assert chamadas[2][2]["dueDate"] == date.today().isoformat()
        assert all(c[1].startswith("https://api-sandbox.asaas.com/v3") and c[3] == "chave" for c in chamadas)

    def test_exige_documento(self, monkeypatch):
        monkeypatch.setattr(
            "payments.gateways.requests.request", lambda *a, **k: self._resposta(200, {"data": []})
        )
        membro = MagicMock(id="m1", cpf=None, cnpj=None)
        with pytest.raises(GatewayError, match="CPF"):
            AsaasGateway("chave")._cliente(membro)

    def test_erro_do_asaas_vira_mensagem(self, monkeypatch):
        monkeypatch.setattr(
            "payments.gateways.requests.request",
            lambda *a, **k: self._resposta(400, {"errors": [{"description": "CPF inválido"}]}),
        )
        with pytest.raises(GatewayError, match="CPF inválido"):
            AsaasGateway("chave")._req("GET", "/customers")


@pytest.mark.django_db
class TestPedidoOnline:
    def _checkout(self, user, membro, **item_kwargs):
        from ecommerce.models import Cart, CartItem, CatalogItem, CatalogItemType
        from ecommerce.views import CartViewSet

        dados = dict(name="Livro de resumos", item_type=CatalogItemType.DIGITAL, price=Decimal("50.00"))
        dados.update(item_kwargs)
        item = CatalogItem.objects.create(**dados)
        cart, _ = Cart.objects.get_or_create(membro=membro)
        CartItem.objects.create(cart=cart, catalog_item=item, quantity=1)
        request = factory.post("/", {"payment_method": "online"}, format="json")
        force_authenticate(request, user=user)
        return CartViewSet.as_view({"post": "checkout"})(request), item

    def test_checkout_online_e_pagamento_conclui_pedido(self, test_tenant, member, simulado):
        from ecommerce.models import Order, OrderStatus
        from payments.views import CobrarPedidoView

        user, membro = member
        with schema_context(test_tenant.schema_name):
            resp, _ = self._checkout(user, membro)
            assert resp.status_code == 201, resp.data
            assert resp.data["status"] == "pending"

            cobranca = _post(CobrarPedidoView, user, {"metodo": "pix"}, pedido_id=resp.data["id"])
            assert cobranca.status_code == 201, cobranca.data
            assert str(cobranca.data["pedido"]) == str(resp.data["id"])
            assert cobranca.data["valor"] == "50.00"

            pago = _post(SimularPagamentoView, user, cobranca_id=cobranca.data["id"])
            assert pago.data["status"] == "paga"
            pedido = Order.objects.get(pk=resp.data["id"])
            assert pedido.status == OrderStatus.FULFILLED
            assert pedido.payment_method == "online"
            assert pedido.stripe_payment_intent_id.startswith("sim_")

            # Pedido pago não gera nova cobrança
            assert _post(CobrarPedidoView, user, {"metodo": "pix"}, pedido_id=pedido.id).status_code == 400

    def test_checkout_online_indisponivel(self, test_tenant, member, sem_simulado):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            resp, _ = self._checkout(user, membro)
            assert resp.status_code == 400

    def test_pedido_de_outro_associado_404(self, test_tenant, member, simulado):
        from ecommerce.models import Order
        from membros.models import Membro
        from payments.views import CobrarPedidoView

        user, _ = member
        with schema_context(test_tenant.schema_name):
            outro = Membro.objects.create(nome_completo="Bruno", email="bruno@teste.org")
            pedido = Order.objects.create(membro=outro, total_amount=Decimal("10.00"))
            assert _post(CobrarPedidoView, user, {"metodo": "pix"}, pedido_id=pedido.id).status_code == 404

    def test_falha_no_fulfillment_nao_desfaz_pagamento(self, test_tenant, member, simulado):
        from ecommerce.models import CatalogItemType, Order, OrderStatus
        from payments.services import cobrar_pedido, confirmar_cobranca

        user, membro = member
        with schema_context(test_tenant.schema_name):
            resp, item = self._checkout(user, membro, item_type=CatalogItemType.MATERIAL, inventory_count=1)
            pedido = Order.objects.get(pk=resp.data["id"])
            cobranca = cobrar_pedido(pedido, "pix")
            item.inventory_count = 0
            item.save()

            confirmar_cobranca(cobranca)
            cobranca.refresh_from_db()
            pedido.refresh_from_db()
            assert cobranca.status == Cobranca.PAGA
            assert pedido.status == OrderStatus.PENDING
            assert "não concluído" in pedido.notes
