"""Newsletter segmentada: campanhas, fila de envio e descadastro."""
import uuid

from django.conf import settings
from django.db import models


class StatusCampanha(models.TextChoices):
    RASCUNHO = "rascunho", "Rascunho"
    ENVIANDO = "enviando", "Enviando"
    ENVIADA = "enviada", "Enviada"
    CANCELADA = "cancelada", "Cancelada"


class Campanha(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assunto = models.CharField(max_length=200)
    corpo = models.TextField(help_text="Texto simples; {nome} vira o primeiro nome do destinatário")
    link = models.URLField(blank=True, default="")
    link_label = models.CharField(max_length=60, blank=True, default="")
    publico = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=StatusCampanha.choices, default=StatusCampanha.RASCUNHO)
    enviada_em = models.DateTimeField(null=True, blank=True)
    concluida_em = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.assunto


class StatusEnvio(models.TextChoices):
    PENDENTE = "pendente", "Na fila"
    ENVIADO = "enviado", "Enviado"
    FALHA = "falha", "Falhou"
    CANCELADO = "cancelado", "Cancelado"


class EnvioCampanha(models.Model):
    campanha = models.ForeignKey(Campanha, on_delete=models.CASCADE, related_name="envios")
    email = models.EmailField()
    nome = models.CharField(max_length=255, blank=True, default="")
    membro = models.ForeignKey("membros.Membro", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    contato = models.ForeignKey("contatos.Contato", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    status = models.CharField(max_length=10, choices=StatusEnvio.choices, default=StatusEnvio.PENDENTE, db_index=True)
    tentativas = models.PositiveSmallIntegerField(default=0)
    erro = models.CharField(max_length=255, blank=True, default="")
    enviado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
        constraints = [models.UniqueConstraint(fields=["campanha", "email"], name="envio_unico_por_campanha")]


class TipoRegua(models.TextChoices):
    BOAS_VINDAS = "boas_vindas", "Boas-vindas ao novo associado"
    INATIVOS = "inativos", "Reengajamento de inativos"
    AUTOR_NAO_SOCIO = "autor_nao_socio", "Convite ao autor aprovado que não é sócio"


class Regua(models.Model):
    """Configuração de uma régua automática de relacionamento (uma linha por tipo)."""

    tipo = models.CharField(max_length=20, choices=TipoRegua.choices, unique=True)
    ativa = models.BooleanField(default=False)
    assunto = models.CharField(max_length=200)
    corpo = models.TextField()
    dias = models.PositiveSmallIntegerField(
        default=0, help_text="Inativos: meses sem atividade. Demais: janela em dias após o gatilho"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["tipo"]

    def __str__(self):
        return self.get_tipo_display()


class EnvioRegua(models.Model):
    tipo = models.CharField(max_length=20, choices=TipoRegua.choices, db_index=True)
    chave = models.CharField(max_length=200, help_text="Identifica o gatilho; impede envio repetido")
    email = models.EmailField()
    nome = models.CharField(max_length=255, blank=True, default="")
    membro = models.ForeignKey(
        "membros.Membro", on_delete=models.SET_NULL, null=True, blank=True, related_name="envios_regua"
    )
    detalhe = models.CharField(max_length=255, blank=True, default="")
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-enviado_em"]
        constraints = [models.UniqueConstraint(fields=["tipo", "chave"], name="envio_regua_unico")]

    def __str__(self):
        return f"{self.get_tipo_display()} → {self.email}"


class Descadastro(models.Model):
    email = models.EmailField(unique=True)
    campanha = models.ForeignKey(Campanha, on_delete=models.SET_NULL, null=True, blank=True, related_name="descadastros")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email
