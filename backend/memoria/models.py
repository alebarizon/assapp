"""
AssApp — Módulo Memória Institucional (PIPE Fase 1)

Hipótese H1: Preservação ATIVA de conhecimento institucional.
Cada registro vincula quem decidiu, o quê, por quê e em qual mandato.
"""
import uuid

from django.conf import settings
from django.db import models


class TipoContextoHistorico(models.TextChoices):
    DECISAO = "decisao", "Decisão"
    PROCESSO = "processo", "Processo"
    EVENTO = "evento", "Evento"
    FINANCEIRO = "financeiro", "Financeiro"
    COMUNICACAO = "comunicacao", "Comunicação"
    FILIACAO = "filiacao", "Filiação"
    EVENTO_ACADEMICO = "evento_academico", "Evento Acadêmico"
    OUTRO = "outro", "Outro"


class ContextoHistorico(models.Model):
    """
    Registro contextualizado de memória institucional (H1).
    Responde: quem decidiu o quê, por quê, em qual mandato.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mandato = models.ForeignKey(
        "mandatos.Mandato",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contextos",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contextos_autor",
    )
    tipo = models.CharField(max_length=25, choices=TipoContextoHistorico.choices)
    titulo = models.CharField(max_length=255)
    conteudo = models.TextField()
    decisao = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="O que foi decidido",
    )
    motivo = models.TextField(
        blank=True,
        null=True,
        help_text="Por que foi decidido — essencial para H1",
    )
    entidade_tipo = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Tipo da entidade vinculada: membro, evento, etc.",
    )
    entidade_id = models.UUIDField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    visivel_diretoria = models.BooleanField(default=True)
    arquivado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contexto Histórico"
        verbose_name_plural = "Contextos Históricos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mandato", "tipo"]),
            models.Index(fields=["entidade_tipo", "entidade_id"]),
        ]

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.mandato_id:
            TimelineInstitucional.objects.create(
                mandato_id=self.mandato_id,
                tipo=self.tipo,
                titulo=self.titulo,
                descricao=self.decisao or self.conteudo[:200],
                data_evento=self.created_at,
                metadata={"contexto_id": str(self.id)},
                contexto_id=self.id,
            )


class TimelineInstitucional(models.Model):
    """Visão cronológica de eventos por mandato."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mandato = models.ForeignKey(
        "mandatos.Mandato",
        on_delete=models.CASCADE,
        related_name="timeline",
    )
    tipo = models.CharField(max_length=50)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    data_evento = models.DateTimeField()
    metadata = models.JSONField(blank=True, null=True)
    contexto_id = models.UUIDField(blank=True, null=True)

    class Meta:
        verbose_name = "Evento na Timeline"
        verbose_name_plural = "Timeline Institucional"
        ordering = ["-data_evento"]
        indexes = [models.Index(fields=["mandato", "data_evento"])]

    def __str__(self):
        return f"{self.data_evento.date()} — {self.titulo}"
