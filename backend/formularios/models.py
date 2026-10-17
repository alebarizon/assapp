"""
Formulários da associação: pesquisas, avaliações de evento, consultas aos associados.

Distribuição:
- Link público aberto (`public_token`) — qualquer pessoa com o link responde.
- Portal do associado (`disponivel_no_portal`) — associados logados respondem uma vez.
- Convite individual — `Resposta` pré-criada por associado, com link pessoal (`Resposta.token`).
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Formulario(models.Model):
    RASCUNHO = "rascunho"
    PUBLICADO = "publicado"
    ENCERRADO = "encerrado"
    STATUS_CHOICES = [
        (RASCUNHO, "Rascunho"),
        (PUBLICADO, "Recebendo respostas"),
        (ENCERRADO, "Encerrado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=RASCUNHO, db_index=True)
    link_publico_ativo = models.BooleanField(
        default=False, help_text="Aceita respostas de qualquer pessoa com o link"
    )
    pedir_identificacao = models.BooleanField(
        default=True, help_text="No link público, exige nome e e-mail de quem responde"
    )
    disponivel_no_portal = models.BooleanField(
        default=False, help_text="Aparece para todos os associados no portal"
    )
    public_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    evento = models.ForeignKey(
        "eventos.EventoAcademico",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="formularios",
        help_text="Evento avaliado por este formulário (opcional)",
    )
    encerra_em = models.DateTimeField(null=True, blank=True)
    mensagem_confirmacao = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="formularios_criados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Formulário"
        verbose_name_plural = "Formulários"
        ordering = ["-created_at"]

    def __str__(self):
        return self.titulo

    @property
    def aceitando_respostas(self) -> bool:
        if self.status != self.PUBLICADO:
            return False
        return not (self.encerra_em and self.encerra_em <= timezone.now())


class Secao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    formulario = models.ForeignKey(Formulario, on_delete=models.CASCADE, related_name="secoes")
    titulo = models.CharField(max_length=200, blank=True, default="")
    descricao = models.TextField(blank=True, default="")
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Seção"
        verbose_name_plural = "Seções"
        ordering = ["ordem", "id"]

    def __str__(self):
        return self.titulo or f"Seção {self.ordem}"


class Pergunta(models.Model):
    TEXTO_CURTO = "texto_curto"
    TEXTO_LONGO = "texto_longo"
    NUMERO = "numero"
    EMAIL = "email"
    DATA = "data"
    ESCOLHA_UNICA = "escolha_unica"
    MULTIPLA_ESCOLHA = "multipla_escolha"
    ESCALA = "escala"
    TIPO_CHOICES = [
        (TEXTO_CURTO, "Texto curto"),
        (TEXTO_LONGO, "Texto longo"),
        (NUMERO, "Número"),
        (EMAIL, "E-mail"),
        (DATA, "Data"),
        (ESCOLHA_UNICA, "Escolha única"),
        (MULTIPLA_ESCOLHA, "Múltipla escolha"),
        (ESCALA, "Escala (nota)"),
    ]
    TIPOS_COM_OPCOES = {ESCOLHA_UNICA, MULTIPLA_ESCOLHA}

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    secao = models.ForeignKey(Secao, on_delete=models.CASCADE, related_name="perguntas")
    texto = models.CharField(max_length=500)
    ajuda = models.CharField(max_length=500, blank=True, default="")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TEXTO_CURTO)
    opcoes = models.JSONField(default=list, blank=True)
    escala_min = models.PositiveSmallIntegerField(default=1)
    escala_max = models.PositiveSmallIntegerField(default=5)
    obrigatoria = models.BooleanField(default=False)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Pergunta"
        verbose_name_plural = "Perguntas"
        ordering = ["ordem", "id"]

    def __str__(self):
        return self.texto[:60]


class Resposta(models.Model):
    """Uma pessoa respondendo um formulário (convite pendente, rascunho ou enviada)."""

    PENDENTE = "pendente"
    EM_ANDAMENTO = "em_andamento"
    ENVIADA = "enviada"
    STATUS_CHOICES = [
        (PENDENTE, "Pendente"),
        (EM_ANDAMENTO, "Em andamento"),
        (ENVIADA, "Enviada"),
    ]

    LINK_PUBLICO = "link_publico"
    PORTAL = "portal"
    CONVITE = "convite"
    ORIGEM_CHOICES = [
        (LINK_PUBLICO, "Link público"),
        (PORTAL, "Portal do associado"),
        (CONVITE, "Convite"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    formulario = models.ForeignKey(Formulario, on_delete=models.CASCADE, related_name="respostas")
    membro = models.ForeignKey(
        "membros.Membro",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="respostas_formularios",
    )
    nome = models.CharField(max_length=200, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES, default=LINK_PUBLICO)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDENTE, db_index=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    enviada_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resposta"
        verbose_name_plural = "Respostas"
        ordering = ["-enviada_em", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["formulario", "membro"],
                condition=models.Q(membro__isnull=False),
                name="formularios_resposta_unica_por_membro",
            )
        ]
        indexes = [models.Index(fields=["formulario", "status"])]

    def __str__(self):
        return f"{self.formulario.titulo} — {self.nome or self.email or 'anônimo'}"


class ItemResposta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resposta = models.ForeignKey(Resposta, on_delete=models.CASCADE, related_name="itens")
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE, related_name="itens")
    valor_texto = models.TextField(blank=True, default="")
    valor_lista = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Item de resposta"
        verbose_name_plural = "Itens de resposta"
        constraints = [
            models.UniqueConstraint(fields=["resposta", "pergunta"], name="formularios_item_unico")
        ]
