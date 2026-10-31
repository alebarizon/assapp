import secrets
import uuid

from django.conf import settings
from django.db import models

EVENTOS = [
    ("membro.criado", "Associado cadastrado"),
    ("anuidade.paga", "Anuidade paga"),
    ("inscricao.criada", "Inscrição em evento"),
]
EVENTOS_VALIDOS = frozenset(e for e, _ in EVENTOS)
EVENTO_TESTE = "ping"


def _novo_segredo():
    return f"whsec_{secrets.token_urlsafe(32)}"


class WebhookSaida(models.Model):
    """Endereço externo (Make, Zapier, n8n, sistema próprio) que recebe os eventos da associação."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=500)
    descricao = models.CharField(max_length=120, blank=True, default="")
    eventos = models.JSONField(default=list)
    segredo = models.CharField(max_length=80, default=_novo_segredo)
    ativo = models.BooleanField(default=True)
    falhas_seguidas = models.PositiveIntegerField(default=0)
    ultima_entrega_em = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Webhook de saída"
        verbose_name_plural = "Webhooks de saída"

    def __str__(self):
        return self.descricao or self.url

    def regenerar_segredo(self):
        self.segredo = _novo_segredo()
        self.save(update_fields=["segredo"])


class EntregaWebhook(models.Model):
    PENDENTE = "pendente"
    ENTREGUE = "entregue"
    DESISTIU = "desistiu"
    STATUS_CHOICES = [(PENDENTE, "Pendente"), (ENTREGUE, "Entregue"), (DESISTIU, "Desistiu")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(WebhookSaida, on_delete=models.CASCADE, related_name="entregas")
    evento = models.CharField(max_length=40)
    dados = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDENTE, db_index=True)
    tentativas = models.PositiveSmallIntegerField(default=0)
    proxima_tentativa = models.DateTimeField(db_index=True)
    resposta_status = models.PositiveSmallIntegerField(null=True, blank=True)
    ultimo_erro = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    entregue_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
