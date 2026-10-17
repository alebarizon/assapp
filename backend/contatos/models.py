"""
Contatos — CRM leve da associação.

Recebe mensagens do site (formulário de contato), interessados em filiação,
imprensa e parceiros; a diretoria acompanha pelo funil e pode converter o
contato em associado.
"""
import uuid

from django.conf import settings
from django.db import models


class Etiqueta(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    cor = models.CharField(max_length=7, blank=True, default="#64748B")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"

    def __str__(self):
        return self.nome


class Contato(models.Model):
    NOVO = "novo"
    EM_ATENDIMENTO = "em_atendimento"
    INTERESSADO = "interessado"
    CONVERTIDO = "convertido"
    ARQUIVADO = "arquivado"
    ETAPA_CHOICES = [
        (NOVO, "Novo"),
        (EM_ATENDIMENTO, "Em atendimento"),
        (INTERESSADO, "Interessado"),
        (CONVERTIDO, "Convertido"),
        (ARQUIVADO, "Arquivado"),
    ]
    ETAPAS_ABERTAS = [NOVO, EM_ATENDIMENTO, INTERESSADO]

    SITE_CONTATO = "site_contato"
    SITE_ASSOCIE_SE = "site_associe_se"
    EVENTO = "evento"
    INDICACAO = "indicacao"
    REDES_SOCIAIS = "redes_sociais"
    MANUAL = "manual"
    ORIGEM_CHOICES = [
        (SITE_CONTATO, "Site — contato"),
        (SITE_ASSOCIE_SE, "Site — associe-se"),
        (EVENTO, "Evento"),
        (INDICACAO, "Indicação"),
        (REDES_SOCIAIS, "Redes sociais"),
        (MANUAL, "Cadastro manual"),
    ]

    ASSUNTO_CHOICES = [
        ("filiacao", "Quero me associar"),
        ("eventos", "Eventos"),
        ("cursos", "Cursos"),
        ("imprensa", "Imprensa"),
        ("parceria", "Parcerias"),
        ("outro", "Outro assunto"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200)
    email = models.EmailField(db_index=True)
    telefone = models.CharField(max_length=40, blank=True, default="")
    instituicao = models.CharField(max_length=255, blank=True, default="")
    assunto = models.CharField(max_length=20, choices=ASSUNTO_CHOICES, default="outro")
    mensagem = models.TextField(blank=True, default="")
    etapa = models.CharField(max_length=20, choices=ETAPA_CHOICES, default=NOVO, db_index=True)
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES, default=SITE_CONTATO)
    etiquetas = models.ManyToManyField(Etiqueta, blank=True, related_name="contatos")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contatos_atribuidos",
    )
    membro = models.ForeignKey(
        "membros.Membro",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contatos",
    )
    consentimento_lgpd = models.BooleanField(default=False)
    ultima_interacao_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"
        indexes = [models.Index(fields=["etapa", "created_at"])]

    def __str__(self):
        return f"{self.nome} <{self.email}>"


class Nota(models.Model):
    MANUAL = "manual"
    SISTEMA = "sistema"
    MENSAGEM = "mensagem"
    TIPO_CHOICES = [
        (MANUAL, "Anotação"),
        (SISTEMA, "Sistema"),
        (MENSAGEM, "Nova mensagem do contato"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contato = models.ForeignKey(Contato, on_delete=models.CASCADE, related_name="notas")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default=MANUAL)
    texto = models.TextField()
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
