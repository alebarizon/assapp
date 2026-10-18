"""
Pagamento online da associação (Pix, cartão, boleto) via gateway.

Cada associação usa a própria conta no gateway: o dinheiro cai direto nela.
"""
import secrets
import uuid

from django.conf import settings
from django.db import models

from .crypto import cifrar, decifrar


def _novo_webhook_token() -> str:
    return secrets.token_urlsafe(32)


class ConfiguracaoPagamento(models.Model):
    """Credenciais do gateway da associação (registro único por schema)."""

    ASAAS = "asaas"
    PROVEDOR_CHOICES = [(ASAAS, "Asaas")]

    provedor = models.CharField(max_length=20, choices=PROVEDOR_CHOICES, default=ASAAS)
    ativo = models.BooleanField(default=False)
    sandbox = models.BooleanField(default=True, help_text="Ambiente de testes do gateway")
    api_key_cifrada = models.TextField(blank=True, default="")
    webhook_token = models.CharField(max_length=64, default=_novo_webhook_token)
    aceita_pix = models.BooleanField(default=True)
    aceita_cartao = models.BooleanField(default=True)
    aceita_boleto = models.BooleanField(default=False)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração de pagamento"
        verbose_name_plural = "Configuração de pagamento"

    def __str__(self):
        return f"{self.get_provedor_display()} ({'ativo' if self.ativo else 'inativo'})"

    @classmethod
    def atual(cls) -> "ConfiguracaoPagamento":
        config = cls.objects.order_by("pk").first()
        return config or cls.objects.create()

    @property
    def api_key(self) -> str:
        return decifrar(self.api_key_cifrada)

    @api_key.setter
    def api_key(self, valor: str):
        self.api_key_cifrada = cifrar(valor) if valor else ""

    @property
    def metodos_aceitos(self) -> list[str]:
        metodos = []
        if self.aceita_pix:
            metodos.append(Cobranca.PIX)
        if self.aceita_cartao:
            metodos.append(Cobranca.CARTAO)
        if self.aceita_boleto:
            metodos.append(Cobranca.BOLETO)
        return metodos


class Cobranca(models.Model):
    """Uma tentativa de cobrança no gateway (o associado pode gerar Pix e depois pagar no cartão)."""

    PIX = "pix"
    CARTAO = "cartao"
    BOLETO = "boleto"
    METODO_CHOICES = [(PIX, "Pix"), (CARTAO, "Cartão de crédito"), (BOLETO, "Boleto")]

    SIMULADO = "simulado"
    PROVEDOR_CHOICES = ConfiguracaoPagamento.PROVEDOR_CHOICES + [(SIMULADO, "Simulado")]

    PENDENTE = "pendente"
    PAGA = "paga"
    CANCELADA = "cancelada"
    FALHOU = "falhou"
    STATUS_CHOICES = [
        (PENDENTE, "Aguardando pagamento"),
        (PAGA, "Paga"),
        (CANCELADA, "Cancelada"),
        (FALHOU, "Falhou"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membro = models.ForeignKey("membros.Membro", on_delete=models.CASCADE, related_name="cobrancas")
    anuidade = models.ForeignKey(
        "membros.Anuidade", on_delete=models.CASCADE, null=True, blank=True, related_name="cobrancas"
    )
    pedido = models.ForeignKey(
        "ecommerce.Order", on_delete=models.CASCADE, null=True, blank=True, related_name="cobrancas"
    )
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=10, choices=METODO_CHOICES)
    provedor = models.CharField(max_length=20, choices=PROVEDOR_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDENTE, db_index=True)
    external_id = models.CharField(max_length=100, blank=True, default="", db_index=True)
    url_pagamento = models.URLField(max_length=500, blank=True, default="")
    pix_copia_cola = models.TextField(blank=True, default="")
    pix_qrcode_base64 = models.TextField(blank=True, default="")
    vencimento = models.DateField()
    pago_em = models.DateTimeField(null=True, blank=True)
    erro = models.TextField(blank=True, default="")
    payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cobrança"
        verbose_name_plural = "Cobranças"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["anuidade", "status"]),
            models.Index(fields=["pedido", "status"]),
        ]

    def __str__(self):
        return f"{self.descricao} — {self.get_metodo_display()} — {self.get_status_display()}"
