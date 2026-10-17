"""
Mensagens — conversas entre a diretoria (secretaria) e cada associado.
"""
import uuid

from django.conf import settings
from django.db import models


class Conversa(models.Model):
    ABERTA = "aberta"
    ARQUIVADA = "arquivada"
    STATUS_CHOICES = [(ABERTA, "Aberta"), (ARQUIVADA, "Arquivada")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membro = models.ForeignKey("membros.Membro", on_delete=models.CASCADE, related_name="conversas")
    assunto = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ABERTA, db_index=True)
    iniciada_pela_diretoria = models.BooleanField(default=True)
    lida_pela_diretoria = models.BooleanField(default=True)
    lida_pelo_associado = models.BooleanField(default=True)
    ultima_mensagem_em = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ultima_mensagem_em"]
        verbose_name = "Conversa"
        verbose_name_plural = "Conversas"

    def __str__(self):
        return f"{self.assunto} — {self.membro}"


class Mensagem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name="mensagens")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    autor_nome = models.CharField(max_length=200)
    da_diretoria = models.BooleanField(default=False)
    texto = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
