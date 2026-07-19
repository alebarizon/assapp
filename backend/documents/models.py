"""Documentos institucionais da associação (adaptado do WellSaaS business.Document)."""
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class DocumentAudience(models.TextChoices):
    GERAL = "geral", "Geral (associação)"
    DIRETORIA = "diretoria", "Diretoria"
    MEMBRO = "membro", "Membro específico"


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="documents/%Y/%m/%d/")
    file_type = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    audience = models.CharField(
        max_length=20,
        choices=DocumentAudience.choices,
        default=DocumentAudience.GERAL,
        db_index=True,
    )
    membro = models.ForeignKey(
        "membros.Membro",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents",
        help_text="Obrigatório quando audience=membro",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["audience", "created_at"]),
            models.Index(fields=["membro", "created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_audience_display()})"

    def clean(self):
        if self.audience == DocumentAudience.MEMBRO and not self.membro_id:
            raise ValidationError({"membro": "Informe o membro para audience=membro."})
        if self.audience != DocumentAudience.MEMBRO:
            self.membro = None

    def save(self, *args, **kwargs):
        if not self.file_type and self.file:
            _, ext = os.path.splitext(self.file.name)
            self.file_type = ext.lstrip(".").lower() if ext else None
        self.full_clean()
        super().save(*args, **kwargs)
