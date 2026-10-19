"""
Gateways de pagamento.

Asaas: https://docs.asaas.com — cliente por associado (externalReference = id do Membro),
cobrança com externalReference = id da Cobranca. Cartão e boleto são pagos na fatura
hospedada pelo Asaas (invoiceUrl); dados de cartão nunca passam pelo Gesttora.

PagBank: https://developer.pagbank.com.br — Pix pela API de Pedidos (reference_id = id da
Cobranca); cartão e boleto pela página do Checkout PagBank.

Mercado Pago: https://www.mercadopago.com.br/developers — Pix pela API de Pagamentos;
cartão e boleto pelo Checkout Pro (preferência). external_reference = id da Cobranca.
Não há sandbox: o modo de teste depende das credenciais (aba "Teste" da aplicação).
"""
import base64
import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

import requests
from django.utils import timezone

PAGO = "pago"
CANCELADO = "cancelado"
PENDENTE = "pendente"


class GatewayError(Exception):
    """Erro com mensagem apresentável ao usuário."""


@dataclass
class ResultadoCobranca:
    external_id: str
    url_pagamento: str = ""
    pix_copia_cola: str = ""
    pix_qrcode_base64: str = ""
    payload: dict = field(default_factory=dict)


def _somente_digitos(valor: str | None) -> str:
    return re.sub(r"\D", "", valor or "")


def _documento(membro) -> str:
    documento = _somente_digitos(membro.cpf) or _somente_digitos(membro.cnpj)
    if not documento:
        raise GatewayError(
            "Para pagar online é preciso ter CPF (ou CNPJ) no cadastro. Peça à secretaria para atualizar."
        )
    return documento


def _centavos(valor) -> int:
    return int((Decimal(valor) * 100).quantize(Decimal("1")))


def _expiracao(horas: int) -> datetime:
    return timezone.localtime(timezone.now() + timedelta(hours=horas)).replace(microsecond=0)


class SimuladoGateway:
    """Sem dinheiro real: gera um Pix fictício e o pagamento é confirmado manualmente pela tela."""

    provedor = "simulado"
    validade_horas = None

    def criar_cobranca(self, cobranca, membro) -> ResultadoCobranca:
        external_id = f"sim_{uuid.uuid4().hex[:16]}"
        resultado = ResultadoCobranca(external_id=external_id, payload={"simulado": True})
        if cobranca.metodo == "pix":
            resultado.pix_copia_cola = f"00020126SIMULADO{external_id}5204000053039865802BR6304ABCD"
        return resultado

    def cancelar_cobranca(self, external_id: str) -> None:
        return None

    def consultar(self, cobranca) -> tuple[str, dict]:
        return PENDENTE, {}

    def testar(self) -> dict:
        return {"ok": True}


class _HttpGateway:
    nome = ""
    validade_horas: int | None = None

    def __init__(self, api_key: str, sandbox: bool = True, timeout: int = 20, notification_url: str = "",
                 retorno_url: str = ""):
        if not api_key:
            raise GatewayError(f"Chave de API do {self.nome} não configurada.")
        self.api_key = api_key
        self.sandbox = sandbox
        self.timeout = timeout
        self.notification_url = notification_url
        self.retorno_url = retorno_url

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "User-Agent": "Gesttora"}

    def _mensagem_erro(self, data: dict) -> str:
        return ""

    def _req(self, method: str, path: str, headers: dict | None = None, **kwargs) -> dict:
        try:
            resp = requests.request(
                method,
                f"{self.base_url}{path}",
                headers={**self._headers(), **(headers or {})},
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise GatewayError(f"Não foi possível falar com o {self.nome}. Tente novamente.") from exc

        if resp.status_code in (401, 403):
            raise GatewayError(f"Chave de API do {self.nome} inválida ou sem permissão.")
        try:
            data = resp.json()
        except ValueError:
            data = {}
        if not isinstance(data, dict):
            data = {"resultados": data}
        if resp.status_code >= 400:
            descricao = self._mensagem_erro(data)
            raise GatewayError(descricao or f"{self.nome} recusou a operação (HTTP {resp.status_code}).")
        return data


class AsaasGateway(_HttpGateway):
    provedor = "asaas"
    nome = "Asaas"
    BILLING_TYPE = {"pix": "PIX", "cartao": "CREDIT_CARD", "boleto": "BOLETO"}
    STATUS_PAGO = {"RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"}
    STATUS_CANCELADO = {"REFUNDED", "REFUND_REQUESTED"}

    def __init__(self, api_key: str, sandbox: bool = True, timeout: int = 20, **kwargs):
        super().__init__(api_key, sandbox=sandbox, timeout=timeout, **kwargs)
        self.base_url = "https://api-sandbox.asaas.com/v3" if sandbox else "https://api.asaas.com/v3"

    def _headers(self) -> dict:
        return {"access_token": self.api_key, "User-Agent": "Gesttora"}

    def _mensagem_erro(self, data: dict) -> str:
        erros = data.get("errors") or []
        return erros[0].get("description") if erros else ""

    def _cliente(self, membro) -> str:
        existentes = self._req("GET", "/customers", params={"externalReference": str(membro.id)})
        if existentes.get("data"):
            return existentes["data"][0]["id"]

        documento = _documento(membro)
        cliente = self._req(
            "POST",
            "/customers",
            json={
                "name": membro.nome_completo,
                "email": membro.email,
                "cpfCnpj": documento,
                "mobilePhone": _somente_digitos(membro.telefone) or None,
                "externalReference": str(membro.id),
                "notificationDisabled": True,
            },
        )
        return cliente["id"]

    def criar_cobranca(self, cobranca, membro) -> ResultadoCobranca:
        vencimento = max(cobranca.vencimento, date.today())
        pagamento = self._req(
            "POST",
            "/payments",
            json={
                "customer": self._cliente(membro),
                "billingType": self.BILLING_TYPE[cobranca.metodo],
                "value": float(cobranca.valor),
                "dueDate": vencimento.isoformat(),
                "description": cobranca.descricao,
                "externalReference": str(cobranca.id),
            },
        )
        resultado = ResultadoCobranca(
            external_id=pagamento["id"],
            url_pagamento=pagamento.get("invoiceUrl") or "",
            payload=pagamento,
        )
        if cobranca.metodo == "pix":
            qr = self._req("GET", f"/payments/{pagamento['id']}/pixQrCode")
            resultado.pix_copia_cola = qr.get("payload") or ""
            resultado.pix_qrcode_base64 = qr.get("encodedImage") or ""
        return resultado

    def cancelar_cobranca(self, external_id: str) -> None:
        self._req("DELETE", f"/payments/{external_id}")

    def consultar(self, cobranca) -> tuple[str, dict]:
        pagamento = self._req("GET", f"/payments/{cobranca.external_id}")
        if pagamento.get("deleted") or pagamento.get("status") in self.STATUS_CANCELADO:
            return CANCELADO, pagamento
        if pagamento.get("status") in self.STATUS_PAGO:
            return PAGO, pagamento
        return PENDENTE, pagamento

    def testar(self) -> dict:
        saldo = self._req("GET", "/finance/balance")
        return {"ok": True, "saldo": saldo.get("balance")}


class PagBankGateway(_HttpGateway):
    provedor = "pagbank"
    nome = "PagBank"
    validade_horas = 72
    CHECKOUT_TIPO = {"cartao": "CREDIT_CARD", "boleto": "BOLETO"}

    def __init__(self, api_key: str, sandbox: bool = True, timeout: int = 20, **kwargs):
        super().__init__(api_key, sandbox=sandbox, timeout=timeout, **kwargs)
        self.base_url = "https://sandbox.api.pagseguro.com" if sandbox else "https://api.pagseguro.com"

    def _mensagem_erro(self, data: dict) -> str:
        erros = data.get("error_messages") or []
        if not erros:
            return ""
        erro = erros[0]
        descricao = erro.get("description") or ""
        campo = erro.get("parameter_name")
        return f"{descricao} ({campo})" if campo else descricao

    def _cliente(self, membro) -> dict:
        return {"name": membro.nome_completo[:120], "email": membro.email, "tax_id": _documento(membro)}

    def _item(self, cobranca) -> dict:
        return {
            "reference_id": str(cobranca.id),
            "name": cobranca.descricao[:64],
            "quantity": 1,
            "unit_amount": _centavos(cobranca.valor),
        }

    def _imagem_qrcode(self, links: list) -> str:
        url = next((l.get("href") for l in links if l.get("rel") == "QRCODE.PNG"), "")
        if not url:
            return ""
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException:
            return ""
        if resp.status_code != 200:
            return ""
        return base64.b64encode(resp.content).decode()

    def criar_cobranca(self, cobranca, membro) -> ResultadoCobranca:
        expiracao = _expiracao(self.validade_horas).isoformat()
        notificacoes = [self.notification_url] if self.notification_url else None

        if cobranca.metodo == "pix":
            pedido = self._req(
                "POST",
                "/orders",
                json={
                    "reference_id": str(cobranca.id),
                    "customer": self._cliente(membro),
                    "items": [self._item(cobranca)],
                    "qr_codes": [{"amount": {"value": _centavos(cobranca.valor)}, "expiration_date": expiracao}],
                    **({"notification_urls": notificacoes} if notificacoes else {}),
                },
            )
            qr = (pedido.get("qr_codes") or [{}])[0]
            return ResultadoCobranca(
                external_id=pedido["id"],
                pix_copia_cola=qr.get("text") or "",
                pix_qrcode_base64=self._imagem_qrcode(qr.get("links") or []),
                payload=pedido,
            )

        checkout = self._req(
            "POST",
            "/checkouts",
            json={
                "reference_id": str(cobranca.id),
                "expiration_date": expiracao,
                "customer": self._cliente(membro),
                "customer_modifiable": True,
                "items": [self._item(cobranca)],
                "payment_methods": [{"type": self.CHECKOUT_TIPO[cobranca.metodo]}],
                **({"payment_notification_urls": notificacoes} if notificacoes else {}),
                **({"redirect_url": self.retorno_url, "return_url": self.retorno_url} if self.retorno_url else {}),
            },
        )
        url = next((l.get("href") for l in checkout.get("links") or [] if l.get("rel") == "PAY"), "")
        return ResultadoCobranca(external_id=checkout["id"], url_pagamento=url or "", payload=checkout)

    def cancelar_cobranca(self, external_id: str) -> None:
        if external_id.startswith("CHEC_"):
            self._req("POST", f"/checkouts/{external_id}/inactivate")

    @staticmethod
    def estado_do_pedido(pedido: dict) -> str:
        status = {c.get("status") for c in pedido.get("charges") or []}
        if "PAID" in status:
            return PAGO
        if status and status <= {"CANCELED", "DECLINED"}:
            return CANCELADO
        return PENDENTE

    def pedido(self, order_id: str) -> dict:
        return self._req("GET", f"/orders/{order_id}")

    def consultar(self, cobranca) -> tuple[str, dict]:
        external_id = cobranca.external_id
        if external_id.startswith("CHEC_"):
            checkout = self._req("GET", f"/checkouts/{external_id}", params={"limit": 100})
            for pedido in checkout.get("orders") or []:
                if self.estado_do_pedido(pedido) == PAGO:
                    return PAGO, pedido
            if checkout.get("status") in ("EXPIRED", "INACTIVE"):
                return CANCELADO, checkout
            return PENDENTE, checkout

        pedido = self.pedido(external_id)
        estado = self.estado_do_pedido(pedido)
        if estado == PENDENTE and not pedido.get("charges"):
            qr = (pedido.get("qr_codes") or [{}])[0]
            expira = qr.get("expiration_date")
            if expira:
                try:
                    if datetime.fromisoformat(expira) < timezone.now():
                        return CANCELADO, pedido
                except ValueError:
                    pass
        return estado, pedido

    def testar(self) -> dict:
        self._req("POST", "/public-keys", json={"type": "card"})
        return {"ok": True}


class MercadoPagoGateway(_HttpGateway):
    provedor = "mercadopago"
    nome = "Mercado Pago"
    validade_horas = 72
    base_url = "https://api.mercadopago.com"
    EXCLUIDOS = {
        "cartao": ["ticket", "bank_transfer", "atm"],
        "boleto": ["credit_card", "debit_card", "prepaid_card", "bank_transfer"],
    }
    STATUS_CANCELADO = {"cancelled", "refunded", "charged_back", "expired"}

    def _mensagem_erro(self, data: dict) -> str:
        causas = data.get("cause") or []
        if causas and isinstance(causas, list) and causas[0].get("description"):
            return causas[0]["description"]
        return data.get("message") or ""

    def _pagador(self, membro) -> dict:
        documento = _documento(membro)
        nome, _, sobrenome = (membro.nome_completo or "").partition(" ")
        return {
            "email": membro.email,
            "first_name": nome,
            "last_name": sobrenome,
            "identification": {"type": "CPF" if len(documento) == 11 else "CNPJ", "number": documento},
        }

    @staticmethod
    def _data(dt: datetime) -> str:
        return dt.isoformat(timespec="milliseconds")

    def criar_cobranca(self, cobranca, membro) -> ResultadoCobranca:
        expiracao = _expiracao(self.validade_horas)
        notificacao = {"notification_url": self.notification_url} if self.notification_url else {}

        if cobranca.metodo == "pix":
            pagamento = self._req(
                "POST",
                "/v1/payments",
                headers={"X-Idempotency-Key": str(cobranca.id)},
                json={
                    "transaction_amount": float(cobranca.valor),
                    "description": cobranca.descricao,
                    "payment_method_id": "pix",
                    "external_reference": str(cobranca.id),
                    "date_of_expiration": self._data(expiracao),
                    "payer": self._pagador(membro),
                    **notificacao,
                },
            )
            dados = (pagamento.get("point_of_interaction") or {}).get("transaction_data") or {}
            return ResultadoCobranca(
                external_id=str(pagamento["id"]),
                url_pagamento=dados.get("ticket_url") or "",
                pix_copia_cola=dados.get("qr_code") or "",
                pix_qrcode_base64=dados.get("qr_code_base64") or "",
                payload=pagamento,
            )

        pagador = self._pagador(membro)
        preferencia = self._req(
            "POST",
            "/checkout/preferences",
            json={
                "items": [
                    {
                        "id": str(cobranca.id),
                        "title": cobranca.descricao[:250],
                        "quantity": 1,
                        "currency_id": "BRL",
                        "unit_price": float(cobranca.valor),
                    }
                ],
                "payer": {
                    "name": pagador["first_name"],
                    "surname": pagador["last_name"],
                    "email": pagador["email"],
                    "identification": pagador["identification"],
                },
                "external_reference": str(cobranca.id),
                "payment_methods": {"excluded_payment_types": [{"id": t} for t in self.EXCLUIDOS[cobranca.metodo]]},
                "expires": True,
                "expiration_date_to": self._data(expiracao),
                **({"back_urls": dict.fromkeys(("success", "pending", "failure"), self.retorno_url)}
                   if self.retorno_url else {}),
                **notificacao,
            },
        )
        return ResultadoCobranca(
            external_id=preferencia["id"],
            url_pagamento=preferencia.get("init_point") or "",
            payload=preferencia,
        )

    def cancelar_cobranca(self, external_id: str) -> None:
        if external_id.isdigit():
            self._req("PUT", f"/v1/payments/{external_id}", json={"status": "cancelled"})
        else:
            self._req(
                "PUT",
                f"/checkout/preferences/{external_id}",
                json={"expires": True, "expiration_date_to": self._data(timezone.localtime().replace(microsecond=0))},
            )

    def pagamento(self, payment_id: str) -> dict:
        return self._req("GET", f"/v1/payments/{payment_id}")

    @classmethod
    def estado_do_pagamento(cls, pagamento: dict) -> str:
        if pagamento.get("status") == "approved":
            return PAGO
        if pagamento.get("status") in cls.STATUS_CANCELADO:
            return CANCELADO
        return PENDENTE

    def consultar(self, cobranca) -> tuple[str, dict]:
        busca = self._req(
            "GET",
            "/v1/payments/search",
            params={"external_reference": str(cobranca.id), "sort": "date_created", "criteria": "desc"},
        )
        pagamentos = busca.get("results") or []
        for pagamento in pagamentos:
            if self.estado_do_pagamento(pagamento) == PAGO:
                return PAGO, pagamento
        if cobranca.metodo == "pix" and pagamentos and all(
            self.estado_do_pagamento(p) == CANCELADO for p in pagamentos
        ):
            return CANCELADO, pagamentos[0]
        return PENDENTE, {}

    def testar(self) -> dict:
        conta = self._req("GET", "/users/me")
        return {"ok": True, "conta": conta.get("nickname") or conta.get("email") or ""}
