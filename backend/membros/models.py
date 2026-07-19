"""
AssApp — Módulo Membros e Filiação

Gestão de associados com histórico de filiações, anuidades e compliance LGPD.
"""
import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


cpf_validator = RegexValidator(
    regex=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{11}$",
    message="CPF inválido. Use formato XXX.XXX.XXX-XX ou 11 dígitos.",
)

cnpj_validator = RegexValidator(
    regex=r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$|^\d{14}$",
    message="CNPJ inválido.",
)


class FiliacaoStatus(models.TextChoices):
    ATIVA = "ativa", "Ativa"
    INADIMPLENTE = "inadimplente", "Inadimplente"
    SUSPENSA = "suspensa", "Suspensa"
    CANCELADA = "cancelada", "Cancelada"
    HONORARIA = "honoraria", "Honorária"


class AnuidadeStatus(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    PAGA = "paga", "Paga"
    VENCIDA = "vencida", "Vencida"
    ISENTA = "isenta", "Isenta"
    CANCELADA = "cancelada", "Cancelada"


class Membro(models.Model):
    """Associado filiado à organização."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Ponte formal User ↔ Membro (login vs quadro associativo)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membro_perfil",
        help_text="Usuário do sistema vinculado a este associado (opcional)",
    )
    nome_completo = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    cpf = models.CharField(
        max_length=14,
        blank=True,
        null=True,
        validators=[cpf_validator],
    )
    cnpj = models.CharField(
        max_length=18,
        blank=True,
        null=True,
        validators=[cnpj_validator],
        help_text="Para instituições filiadas",
    )
    telefone = models.CharField(max_length=20, blank=True, null=True)
    instituicao = models.CharField(max_length=255, blank=True, null=True)
    area_atuacao = models.CharField(max_length=255, blank=True, null=True)
    lattes_url = models.URLField(blank=True, null=True)
    orcid = models.CharField(max_length=19, blank=True, null=True)
    consentimento_lgpd = models.BooleanField(default=False)
    consentimento_em = models.DateTimeField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Membro"
        verbose_name_plural = "Membros"
        ordering = ["nome_completo"]
        indexes = [models.Index(fields=["cpf"])]

    def __str__(self):
        return self.nome_completo

    @property
    def filiacao_ativa(self):
        return self.filiacoes.filter(status=FiliacaoStatus.ATIVA).first()


class Filiacao(models.Model):
    """Histórico de filiação de um membro."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membro = models.ForeignKey(
        Membro, on_delete=models.CASCADE, related_name="filiacoes"
    )
    mandato = models.ForeignKey(
        "mandatos.Mandato",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="filiacoes",
    )
    tipo = models.CharField(
        max_length=20,
        default="efetivo",
        choices=[
            ("efetivo", "Efetivo"),
            ("estudante", "Estudante"),
            ("honorario", "Honorário"),
            ("institucional", "Institucional"),
        ],
    )
    status = models.CharField(
        max_length=20,
        choices=FiliacaoStatus.choices,
        default=FiliacaoStatus.ATIVA,
        db_index=True,
    )
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Filiação"
        verbose_name_plural = "Filiações"
        indexes = [models.Index(fields=["membro", "status"])]

    def __str__(self):
        return f"{self.membro.nome_completo} — {self.get_status_display()}"


class Anuidade(models.Model):
    """Cobrança de anuidade vinculada a uma filiação."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filiacao = models.ForeignKey(
        Filiacao, on_delete=models.CASCADE, related_name="anuidades"
    )
    ano_referencia = models.PositiveIntegerField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=AnuidadeStatus.choices,
        default=AnuidadeStatus.PENDENTE,
    )
    pago_em = models.DateTimeField(blank=True, null=True)
    nf_numero = models.CharField(max_length=50, blank=True, null=True)
    stripe_payment_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Anuidade"
        verbose_name_plural = "Anuidades"
        unique_together = [["filiacao", "ano_referencia"]]

    def __str__(self):
        return f"Anuidade {self.ano_referencia} — {self.filiacao.membro.nome_completo}"
