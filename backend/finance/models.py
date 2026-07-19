"""
AssApp — Financeiro OSC (adaptado do WellSaaS).

Categorias para associações científicas / terceiro setor.
Anuidades em membros.Anuidade podem espelhar Transaction income.
"""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class TransactionType(models.TextChoices):
    INCOME = "income", "Receita"
    EXPENSE = "expense", "Despesa"


class IncomeCategory(models.TextChoices):
    ANUIDADE = "anuidade", "Anuidade"
    EVENTO = "evento", "Evento / inscrição"
    DOACAO = "doacao", "Doação"
    PATROCINIO = "patrocinio", "Patrocínio"
    OUTROS = "outros", "Outros"


class ExpenseCategory(models.TextChoices):
    ADMINISTRATIVA = "administrativa", "Administrativa"
    EVENTO = "evento", "Evento"
    COMUNICACAO = "comunicacao", "Comunicação / publicação"
    IMPOSTOS = "impostos", "Impostos / taxas"
    OUTROS = "outros", "Outros"


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        help_text="Usuário que lançou (auditoria)",
    )
    mandato = models.ForeignKey(
        "mandatos.Mandato",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    type = models.CharField(max_length=20, choices=TransactionType.choices, db_index=True)
    category = models.CharField(max_length=50, db_index=True)
    occurred_at = models.DateTimeField(db_index=True)
    # Idempotência p/ espelho de anuidade (e futuros gateways)
    referencia = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="Ex: anuidade:<uuid>",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
        ordering = ["-occurred_at", "-created_at"]
        indexes = [
            models.Index(fields=["type", "occurred_at"]),
            models.Index(fields=["category", "occurred_at"]),
        ]

    def __str__(self):
        return f"{self.get_type_display()}: {self.description} — R$ {self.amount}"

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "O valor deve ser maior que zero."})
        if self.type == TransactionType.INCOME:
            valid = {c.value for c in IncomeCategory}
        elif self.type == TransactionType.EXPENSE:
            valid = {c.value for c in ExpenseCategory}
        else:
            valid = set()
        if self.category and self.category not in valid:
            raise ValidationError({"category": f"Categoria inválida para {self.type}."})
        if not self.category:
            raise ValidationError({"category": "A categoria é obrigatória."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
