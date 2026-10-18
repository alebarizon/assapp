"""
Gateways de pagamento.

Asaas: https://docs.asaas.com — cliente por associado (externalReference = id do Membro),
cobrança com externalReference = id da Cobranca. Cartão e boleto são pagos na fatura
hospedada pelo Asaas (invoiceUrl); dados de cartão nunca passam pelo Gesttora.
"""
import re
import uuid
from dataclasses import dataclass, field
from datetime import date

import requests


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


class SimuladoGateway:
    """Sem dinheiro real: gera um Pix fictício e o pagamento é confirmado manualmente pela tela."""

    provedor = "simulado"

    def criar_cobranca(self, cobranca, membro) -> ResultadoCobranca:
        external_id = f"sim_{uuid.uuid4().hex[:16]}"
        resultado = ResultadoCobranca(external_id=external_id, payload={"simulado": True})
        if cobranca.metodo == "pix":
            resultado.pix_copia_cola = f"00020126SIMULADO{external_id}5204000053039865802BR6304ABCD"
        return resultado

    def cancelar_cobranca(self, external_id: str) -> None:
        return None

    def testar(self) -> dict:
        return {"ok": True}


class AsaasGateway:
    provedor = "asaas"
    BILLING_TYPE = {"pix": "PIX", "cartao": "CREDIT_CARD", "boleto": "BOLETO"}

    def __init__(self, api_key: str, sandbox: bool = True, timeout: int = 20):
        if not api_key:
            raise GatewayError("Chave de API do Asaas não configurada.")
        self.api_key = api_key
        self.base_url = "https://api-sandbox.asaas.com/v3" if sandbox else "https://api.asaas.com/v3"
        self.timeout = timeout

    def _req(self, method: str, path: str, **kwargs) -> dict:
        try:
            resp = requests.request(
                method,
                f"{self.base_url}{path}",
                headers={"access_token": self.api_key, "User-Agent": "Gesttora"},
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise GatewayError("Não foi possível falar com o Asaas. Tente novamente.") from exc

        if resp.status_code == 401:
            raise GatewayError("Chave de API do Asaas inválida.")
        try:
            data = resp.json()
        except ValueError:
            data = {}
        if resp.status_code >= 400:
            erros = data.get("errors") or []
            descricao = erros[0].get("description") if erros else ""
            raise GatewayError(descricao or f"Asaas recusou a operação (HTTP {resp.status_code}).")
        return data

    def _cliente(self, membro) -> str:
        existentes = self._req("GET", "/customers", params={"externalReference": str(membro.id)})
        if existentes.get("data"):
            return existentes["data"][0]["id"]

        documento = _somente_digitos(membro.cpf) or _somente_digitos(membro.cnpj)
        if not documento:
            raise GatewayError(
                "Para pagar online é preciso ter CPF (ou CNPJ) no cadastro. Peça à secretaria para atualizar."
            )
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

    def testar(self) -> dict:
        saldo = self._req("GET", "/finance/balance")
        return {"ok": True, "saldo": saldo.get("balance")}
