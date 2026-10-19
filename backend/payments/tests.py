"""Testes do pagamento online de anuidades."""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from finance.models import Transaction
from membros.models import Anuidade, AnuidadeStatus, Filiacao, FiliacaoStatus
from payments.gateways import PAGO, AsaasGateway, GatewayError, MercadoPagoGateway, PagBankGateway
from payments.models import Cobranca, ConfiguracaoPagamento
from payments.views import (
    CobrarAnuidadeView,
    ConfiguracaoPagamentoView,
    DisponibilidadeView,
    MinhaCobrancaView,
    SimularPagamentoView,
    WebhookAsaasView,
    WebhookMercadoPagoView,
    WebhookPagBankView,
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


def _resposta(status_code, json_data, content=b""):
    resp = MagicMock(status_code=status_code, content=content)
    resp.json.return_value = json_data
    return resp


def _membro_fake(**kwargs):
    dados = dict(id="m1", nome_completo="Ana Maria Souza", email="ana@x.org", cpf="123.456.789-09", cnpj=None, telefone="")
    dados.update(kwargs)
    return MagicMock(**dados)


def _cobranca_fake(metodo="pix", **kwargs):
    dados = dict(id="c1", metodo=metodo, valor=Decimal("80.50"), vencimento=date(2020, 1, 1), descricao="Anuidade 2026")
    dados.update(kwargs)
    return MagicMock(**dados)


class _Gravador:
    def __init__(self, *respostas):
        self.respostas = iter(respostas)
        self.chamadas = []

    def __call__(self, method, url, **kwargs):
        self.chamadas.append({"method": method, "url": url, **kwargs})
        return next(self.respostas)


class TestPagBankGateway:
    def test_pix_cria_pedido_com_qrcode(self, monkeypatch):
        gravador = _Gravador(
            _resposta(201, {
                "id": "ORDE_1",
                "qr_codes": [{"text": "000201PAGBANK", "links": [{"rel": "QRCODE.PNG", "href": "https://pb/qr.png"}]}],
            })
        )
        monkeypatch.setattr("payments.gateways.requests.request", gravador)
        monkeypatch.setattr("payments.gateways.requests.get", lambda *a, **k: _resposta(200, {}, content=b"PNG"))

        gateway = PagBankGateway("tok", sandbox=True, notification_url="https://x/webhook")
        resultado = gateway.criar_cobranca(_cobranca_fake(), _membro_fake())

        chamada = gravador.chamadas[0]
        assert chamada["url"] == "https://sandbox.api.pagseguro.com/orders"
        assert chamada["headers"]["Authorization"] == "Bearer tok"
        assert chamada["json"]["reference_id"] == "c1"
        assert chamada["json"]["customer"]["tax_id"] == "12345678909"
        assert chamada["json"]["qr_codes"][0]["amount"]["value"] == 8050
        assert chamada["json"]["notification_urls"] == ["https://x/webhook"]
        assert resultado.external_id == "ORDE_1"
        assert resultado.pix_copia_cola == "000201PAGBANK"
        assert resultado.pix_qrcode_base64 == "UE5H"

    def test_cartao_usa_checkout_hospedado_sem_notificacao_em_http(self, monkeypatch):
        gravador = _Gravador(
            _resposta(201, {"id": "CHEC_1", "links": [{"rel": "PAY", "href": "https://pagamento.pagbank/x"}]})
        )
        monkeypatch.setattr("payments.gateways.requests.request", gravador)

        resultado = PagBankGateway("tok", sandbox=False).criar_cobranca(_cobranca_fake("cartao"), _membro_fake())

        chamada = gravador.chamadas[0]
        assert chamada["url"] == "https://api.pagseguro.com/checkouts"
        assert chamada["json"]["payment_methods"] == [{"type": "CREDIT_CARD"}]
        assert "payment_notification_urls" not in chamada["json"]
        assert resultado.external_id == "CHEC_1"
        assert resultado.url_pagamento == "https://pagamento.pagbank/x"

    def test_erro_vira_mensagem(self, monkeypatch):
        monkeypatch.setattr(
            "payments.gateways.requests.request",
            lambda *a, **k: _resposta(400, {"error_messages": [{"description": "invalid", "parameter_name": "customer.tax_id"}]}),
        )
        with pytest.raises(GatewayError, match="customer.tax_id"):
            PagBankGateway("tok").criar_cobranca(_cobranca_fake(), _membro_fake())

    def test_estado_do_pedido(self):
        assert PagBankGateway.estado_do_pedido({"charges": [{"status": "PAID"}]}) == "pago"
        assert PagBankGateway.estado_do_pedido({"charges": [{"status": "CANCELED"}]}) == "cancelado"
        assert PagBankGateway.estado_do_pedido({"charges": []}) == "pendente"


class TestMercadoPagoGateway:
    def test_pix_com_idempotencia(self, monkeypatch):
        gravador = _Gravador(
            _resposta(201, {
                "id": 555,
                "point_of_interaction": {"transaction_data": {"qr_code": "000201MP", "qr_code_base64": "iVBOR"}},
            })
        )
        monkeypatch.setattr("payments.gateways.requests.request", gravador)

        resultado = MercadoPagoGateway("APP_USR-x").criar_cobranca(_cobranca_fake(), _membro_fake())

        chamada = gravador.chamadas[0]
        assert chamada["url"] == "https://api.mercadopago.com/v1/payments"
        assert chamada["headers"]["X-Idempotency-Key"] == "c1"
        assert chamada["json"]["payment_method_id"] == "pix"
        assert chamada["json"]["external_reference"] == "c1"
        assert chamada["json"]["payer"]["identification"] == {"type": "CPF", "number": "12345678909"}
        assert chamada["json"]["payer"]["first_name"] == "Ana"
        assert resultado.external_id == "555"
        assert resultado.pix_copia_cola == "000201MP"
        assert resultado.pix_qrcode_base64 == "iVBOR"

    def test_boleto_usa_checkout_pro_sem_cartao(self, monkeypatch):
        gravador = _Gravador(_resposta(201, {"id": "123-abc", "init_point": "https://mp/checkout"}))
        monkeypatch.setattr("payments.gateways.requests.request", gravador)

        resultado = MercadoPagoGateway("tok").criar_cobranca(_cobranca_fake("boleto"), _membro_fake())

        corpo = gravador.chamadas[0]["json"]
        excluidos = {t["id"] for t in corpo["payment_methods"]["excluded_payment_types"]}
        assert {"credit_card", "debit_card"} <= excluidos and "ticket" not in excluidos
        assert corpo["expires"] is True
        assert resultado.external_id == "123-abc"
        assert resultado.url_pagamento == "https://mp/checkout"

    def test_consultar_aprovado_pela_referencia(self, monkeypatch):
        gravador = _Gravador(_resposta(200, {"results": [{"id": 1, "status": "rejected"}, {"id": 2, "status": "approved"}]}))
        monkeypatch.setattr("payments.gateways.requests.request", gravador)

        estado, pagamento = MercadoPagoGateway("tok").consultar(_cobranca_fake("cartao"))
        assert estado == "pago" and pagamento["id"] == 2
        assert gravador.chamadas[0]["params"]["external_reference"] == "c1"

    def test_token_invalido(self, monkeypatch):
        monkeypatch.setattr("payments.gateways.requests.request", lambda *a, **k: _resposta(401, {}))
        with pytest.raises(GatewayError, match="inválida"):
            MercadoPagoGateway("tok").testar()


@pytest.mark.django_db
class TestTrocaDeProvedor:
    def _put(self, user, dados):
        request = factory.put("/", dados, format="json")
        force_authenticate(request, user=user)
        return ConfiguracaoPagamentoView.as_view()(request)

    def test_trocar_provedor_exige_nova_chave(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            assert self._put(board_user, {"api_key": "$aact_1234", "ativo": True}).status_code == 200

            resp = self._put(board_user, {"provedor": "pagbank"})
            assert resp.status_code == 400
            assert "novo provedor" in str(resp.data["api_key"])

            resp = self._put(board_user, {"provedor": "pagbank", "api_key": "pb-token-9876"})
            assert resp.status_code == 200, resp.data
            assert resp.data["provedor"] == "pagbank"
            assert resp.data["api_key_final"] == "…9876"
            assert "/webhook/pagbank/" in resp.data["webhook_url"]
            assert f"token={resp.data['webhook_token']}" in resp.data["webhook_url"]

    def test_trocar_provedor_inativo_descarta_chave_antiga(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            self._put(board_user, {"api_key": "$aact_1234"})
            resp = self._put(board_user, {"provedor": "mercadopago"})
            assert resp.status_code == 200
            assert resp.data["tem_api_key"] is False


@pytest.mark.django_db
class TestWebhooksComToken:
    def _config(self, provedor):
        config = ConfiguracaoPagamento.atual()
        config.provedor = provedor
        config.api_key = "tok"
        config.ativo = True
        config.save()
        return config

    def _cobranca(self, membro, anuidade, provedor, external_id, metodo=Cobranca.PIX):
        return Cobranca.objects.create(
            membro=membro, anuidade=anuidade, descricao="Anuidade 2026", valor=anuidade.valor,
            metodo=metodo, provedor=provedor, external_id=external_id, vencimento=anuidade.vencimento,
        )

    def test_pagbank_rele_pedido_e_quita(self, test_tenant, member, monkeypatch):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            token = self._config("pagbank").webhook_token
            anuidade = _anuidade(membro)
            cobranca = self._cobranca(membro, anuidade, "pagbank", "ORDE_9")
        monkeypatch.setattr(
            PagBankGateway, "pedido",
            lambda self, order_id: {"id": order_id, "reference_id": str(cobranca.id), "charges": [{"status": "PAID"}]},
        )

        request = factory.post(f"/?schema=teste&token={token}", {"id": "ORDE_9", "charges": []}, format="json")
        resp = WebhookPagBankView.as_view()(request)
        assert resp.status_code == 200, resp.data
        assert resp.data["resultado"] == "pago"
        with schema_context(test_tenant.schema_name):
            anuidade.refresh_from_db()
            assert anuidade.status == AnuidadeStatus.PAGA

    def test_pagbank_checkout_acha_cobranca_pelo_item(self, test_tenant, member, monkeypatch):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            token = self._config("pagbank").webhook_token
            anuidade = _anuidade(membro)
            cobranca = self._cobranca(membro, anuidade, "pagbank", "CHEC_1", metodo=Cobranca.CARTAO)
        pedido = {"id": "ORDE_X", "reference_id": "outro", "items": [{"reference_id": str(cobranca.id)}],
                  "charges": [{"status": "DECLINED"}]}
        monkeypatch.setattr(PagBankGateway, "pedido", lambda self, order_id: pedido)

        request = factory.post(f"/?schema=teste&token={token}", {"id": "ORDE_X"}, format="json")
        assert WebhookPagBankView.as_view()(request).data["resultado"] == "ignorado"

        pedido["charges"] = [{"status": "PAID"}]
        request = factory.post(f"/?schema=teste&token={token}", {"id": "ORDE_X"}, format="json")
        assert WebhookPagBankView.as_view()(request).data["resultado"] == "pago"

    def test_token_errado(self, test_tenant):
        with schema_context(test_tenant.schema_name):
            self._config("pagbank")
        request = factory.post("/?schema=teste&token=errado", {"id": "ORDE_1"}, format="json")
        assert WebhookPagBankView.as_view()(request).status_code == 403

    def test_mercadopago_usa_so_o_id_do_pagamento(self, test_tenant, member, monkeypatch):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            token = self._config("mercadopago").webhook_token
            anuidade = _anuidade(membro)
            cobranca = self._cobranca(membro, anuidade, "mercadopago", "pref-1", metodo=Cobranca.CARTAO)
        monkeypatch.setattr(
            MercadoPagoGateway, "pagamento",
            lambda self, pid: {"id": int(pid), "status": "approved", "external_reference": str(cobranca.id)},
        )

        request = factory.post(
            f"/?schema=teste&token={token}", {"type": "payment", "data": {"id": "777"}, "status": "fake"}, format="json"
        )
        resp = WebhookMercadoPagoView.as_view()(request)
        assert resp.data["resultado"] == "pago"
        with schema_context(test_tenant.schema_name):
            cobranca.refresh_from_db()
            assert cobranca.status == Cobranca.PAGA


@pytest.mark.django_db
class TestSincronizacao:
    def test_portal_consulta_gateway_quando_webhook_nao_chega(self, test_tenant, member, monkeypatch):
        from django.utils import timezone

        user, membro = member
        with schema_context(test_tenant.schema_name):
            config = ConfiguracaoPagamento.atual()
            config.provedor, config.api_key, config.ativo = "mercadopago", "tok", True
            config.save()
            anuidade = _anuidade(membro)
            cobranca = Cobranca.objects.create(
                membro=membro, anuidade=anuidade, descricao="Anuidade 2026", valor=anuidade.valor,
                metodo=Cobranca.PIX, provedor="mercadopago", external_id="555", vencimento=anuidade.vencimento,
            )
            consultas = []
            monkeypatch.setattr(
                MercadoPagoGateway, "consultar",
                lambda self, c: consultas.append(c.pk) or (PAGO, {"id": 555, "status": "approved"}),
            )

            request = factory.get("/")
            force_authenticate(request, user=user)
            resp = MinhaCobrancaView.as_view()(request, cobranca_id=cobranca.id)
            assert resp.data["status"] == "pendente"
            assert consultas == []

            Cobranca.objects.filter(pk=cobranca.pk).update(updated_at=timezone.now() - timedelta(minutes=1))
            resp = MinhaCobrancaView.as_view()(request, cobranca_id=cobranca.id)
            assert resp.data["status"] == "paga"
            anuidade.refresh_from_db()
            assert anuidade.status == AnuidadeStatus.PAGA

    def test_varredura_ignora_outro_provedor(self, test_tenant, member, monkeypatch):
        from payments.services import sincronizar_pendentes

        _, membro = member
        with schema_context(test_tenant.schema_name):
            config = ConfiguracaoPagamento.atual()
            config.provedor, config.api_key, config.ativo = "pagbank", "tok", True
            config.save()
            anuidade = _anuidade(membro)
            Cobranca.objects.create(
                membro=membro, anuidade=anuidade, descricao="Anuidade 2026", valor=anuidade.valor,
                metodo=Cobranca.PIX, provedor="asaas", external_id="pay_1", vencimento=anuidade.vencimento,
            )
            monkeypatch.setattr(PagBankGateway, "consultar", lambda self, c: pytest.fail("não deveria consultar"))
            assert sincronizar_pendentes() == {"pago": 0, "cancelado": 0, "pendente": 0}
