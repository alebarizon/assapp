"""
AssApp — Módulo Eventos Acadêmicos (PIPE Fase 1)

Hipótese H3: Integração nativa entre gestão de membros, eventos e fluxo
de submissão/publicação de trabalhos científicos.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class EventoAcademicoStatus(models.TextChoices):
    RASCUNHO = "rascunho", "Rascunho"
    INSCRICOES_ABERTAS = "inscricoes_abertas", "Inscrições Abertas"
    CFP_ABERTO = "cfp_aberto", "Call for Papers Aberto"
    EM_AVALIACAO = "em_avaliacao", "Em Avaliação"
    ENCERRADO = "encerrado", "Encerrado"
    ANAIS_PUBLICADOS = "anais_publicados", "Anais Publicados"
    CANCELADO = "cancelado", "Cancelado"


class SubmissaoStatus(models.TextChoices):
    RASCUNHO = "rascunho", "Rascunho"
    SUBMETIDO = "submetido", "Submetido"
    EM_PARECER = "em_parecer", "Em Parecer"
    ACEITO = "aceito", "Aceito"
    ACEITO_COM_REVISOES = "aceito_com_revisoes", "Aceito com Revisões"
    REJEITADO = "rejeitado", "Rejeitado"
    RETIRADO = "retirado", "Retirado"


class RecomendacaoParecer(models.TextChoices):
    ACEITAR = "aceitar", "Aceitar"
    ACEITAR_COM_REVISOES = "aceitar_com_revisoes", "Aceitar com Revisões"
    REJEITAR = "rejeitar", "Rejeitar"


class EventoAcademico(models.Model):
    """Evento científico integrado ao mandato e quadro de membros (H3)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mandato = models.ForeignKey(
        "mandatos.Mandato",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos",
    )
    titulo = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    descricao = models.TextField(blank=True, null=True)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    local = models.CharField(max_length=255, blank=True, null=True)
    modalidade = models.CharField(
        max_length=20,
        default="presencial",
        choices=[
            ("presencial", "Presencial"),
            ("online", "Online"),
            ("hibrido", "Híbrido"),
        ],
    )
    status = models.CharField(
        max_length=25,
        choices=EventoAcademicoStatus.choices,
        default=EventoAcademicoStatus.RASCUNHO,
        db_index=True,
    )
    capacidade_max = models.PositiveIntegerField(blank=True, null=True)
    valor_inscricao = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    certificado_habilitado = models.BooleanField(default=True)
    carga_horaria = models.PositiveSmallIntegerField(
        blank=True, null=True, help_text="Horas impressas no certificado de participação"
    )
    publicado_site = models.BooleanField(
        default=False, help_text="Exibe o hotsite do evento em /site/eventos"
    )
    resumo = models.CharField(max_length=300, blank=True, default="")
    capa = models.ImageField(upload_to="eventos/capas/%Y/%m/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evento Acadêmico"
        verbose_name_plural = "Eventos Acadêmicos"
        ordering = ["-data_inicio"]
        indexes = [models.Index(fields=["status", "data_inicio"])]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)


class CallForPapers(models.Model):
    """Chamada de trabalhos vinculada a um evento."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evento = models.OneToOneField(
        EventoAcademico,
        on_delete=models.CASCADE,
        related_name="call_for_papers",
    )
    titulo = models.CharField(max_length=255)
    instrucoes = models.TextField()
    data_abertura = models.DateTimeField()
    data_fechamento = models.DateTimeField()
    areas_tematicas = models.JSONField(default=list, blank=True)
    max_submissoes_por_autor = models.PositiveSmallIntegerField(default=2)
    anonimo = models.BooleanField(
        default=True,
        help_text="Parecer duplo-cego",
    )
    criterios = models.JSONField(
        default=list,
        blank=True,
        help_text='Critérios de avaliação: [{"nome": "Relevância", "peso": 2}, ...] — notas de 1 a 5',
    )
    nota_corte = models.DecimalField(
        max_digits=3, decimal_places=2, blank=True, null=True, help_text="Nota média mínima sugerida (1 a 5)"
    )
    exige_arquivo = models.BooleanField(default=False, help_text="Submissão precisa de arquivo (PDF)")

    class Meta:
        verbose_name = "Call for Papers"
        verbose_name_plural = "Calls for Papers"

    def __str__(self):
        return f"CFP: {self.evento.titulo}"


class SubmissaoTrabalho(models.Model):
    """Submissão de trabalho científico."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cfp = models.ForeignKey(
        CallForPapers,
        on_delete=models.CASCADE,
        related_name="submissoes",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissoes",
    )
    membro = models.ForeignKey(
        "membros.Membro",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissoes",
    )
    titulo = models.CharField(max_length=500)
    resumo = models.TextField()
    palavras_chave = models.JSONField(default=list, blank=True)
    coautores = models.JSONField(
        default=list, blank=True, help_text='[{"nome": "...", "email": "...", "instituicao": "..."}]'
    )
    area_tematica = models.CharField(max_length=100, blank=True, null=True)
    arquivo = models.FileField(
        upload_to="eventos/submissoes/%Y/%m/",
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=25,
        choices=SubmissaoStatus.choices,
        default=SubmissaoStatus.RASCUNHO,
    )
    submetido_em = models.DateTimeField(blank=True, null=True)
    decisao_comentario = models.TextField(blank=True, default="")
    decidido_em = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Submissão de Trabalho"
        verbose_name_plural = "Submissões de Trabalhos"
        indexes = [models.Index(fields=["cfp", "status"])]

    def __str__(self):
        return self.titulo


class Parecer(models.Model):
    """Avaliação de submissão por parecerista."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submissao = models.ForeignKey(
        SubmissaoTrabalho,
        on_delete=models.CASCADE,
        related_name="pareceres",
    )
    parecerista = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pareceres",
    )
    recomendacao = models.CharField(
        max_length=25,
        choices=RecomendacaoParecer.choices,
        blank=True,
        null=True,
    )
    nota = models.PositiveSmallIntegerField(blank=True, null=True)
    notas = models.JSONField(default=dict, blank=True, help_text="Nota (1 a 5) por critério da chamada")
    nota_ponderada = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    prazo = models.DateField(blank=True, null=True)
    comentarios_autor = models.TextField(blank=True, null=True)
    comentarios_internos = models.TextField(blank=True, null=True)
    concluido = models.BooleanField(default=False)
    concluido_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Parecer"
        verbose_name_plural = "Pareceres"
        unique_together = [["submissao", "parecerista"]]

    def __str__(self):
        return f"Parecer — {self.submissao.titulo[:50]}"


class InscricaoEvento(models.Model):
    """Inscrição em evento científico."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evento = models.ForeignKey(
        EventoAcademico,
        on_delete=models.CASCADE,
        related_name="inscricoes",
    )
    membro = models.ForeignKey(
        "membros.Membro",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inscricoes_evento",
    )
    nome = models.CharField(max_length=255)
    email = models.EmailField()
    confirmada = models.BooleanField(default=False)
    pago_em = models.DateTimeField(blank=True, null=True)
    certificado = models.FileField(
        upload_to="eventos/certificados/%Y/%m/",
        blank=True,
        null=True,
    )
    presente = models.BooleanField(default=False)
    certificado_codigo = models.CharField(max_length=16, blank=True, null=True, unique=True)
    certificado_emitido_em = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inscrição em Evento"
        verbose_name_plural = "Inscrições em Eventos"
        indexes = [models.Index(fields=["evento", "confirmada"])]

    def __str__(self):
        return f"{self.nome} — {self.evento.titulo}"


class AnaisPublicacao(models.Model):
    """Publicação de anais do evento."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evento = models.OneToOneField(
        EventoAcademico,
        on_delete=models.CASCADE,
        related_name="anais",
    )
    LICENCA_CHOICES = [
        ("cc-by", "CC BY 4.0"),
        ("cc-by-sa", "CC BY-SA 4.0"),
        ("cc-by-nc", "CC BY-NC 4.0"),
        ("cc-by-nc-nd", "CC BY-NC-ND 4.0"),
        ("reservados", "Todos os direitos reservados"),
    ]

    titulo = models.CharField(max_length=255)
    issn = models.CharField(max_length=20, blank=True, null=True)
    isbn = models.CharField(max_length=20, blank=True, default="")
    doi_prefix = models.CharField(max_length=50, blank=True, null=True)
    url_publicacao = models.URLField(blank=True, null=True)
    licenca = models.CharField(max_length=15, choices=LICENCA_CHOICES, default="cc-by")
    apresentacao = models.TextField(blank=True, default="")
    editores = models.CharField(max_length=255, blank=True, default="")
    cidade = models.CharField(max_length=100, blank=True, default="", help_text="Local de publicação (citação ABNT)")
    publicado_em = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Publicação de Anais"
        verbose_name_plural = "Publicações de Anais"

    def __str__(self):
        return f"Anais: {self.evento.titulo}"


class TrabalhoPublicado(models.Model):
    """Trabalho nos anais, com endereço público fixo. Sobrevive à exclusão da submissão."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anais = models.ForeignKey(AnaisPublicacao, on_delete=models.CASCADE, related_name="trabalhos")
    submissao = models.OneToOneField(
        SubmissaoTrabalho, on_delete=models.SET_NULL, null=True, blank=True, related_name="publicacao"
    )
    slug = models.SlugField(max_length=120)
    ordem = models.PositiveIntegerField(default=0)
    titulo = models.CharField(max_length=500)
    resumo = models.TextField()
    palavras_chave = models.JSONField(default=list, blank=True)
    autores = models.JSONField(default=list, help_text='[{"nome": "...", "instituicao": "...", "orcid": "..."}]')
    area_tematica = models.CharField(max_length=100, blank=True, default="")
    arquivo = models.FileField(upload_to="eventos/anais/%Y/", blank=True, null=True)
    doi = models.CharField(max_length=100, blank=True, default="")
    publicado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["ordem", "titulo"]
        constraints = [models.UniqueConstraint(fields=["anais", "slug"], name="trabalho_publicado_slug_unico")]

    def __str__(self):
        return self.titulo


class AtividadeProgramacao(models.Model):
    """Item da grade do evento (palestra, mesa, sessão de trabalhos...)."""

    TIPO_CHOICES = [
        ("abertura", "Abertura / encerramento"),
        ("palestra", "Palestra / conferência"),
        ("mesa", "Mesa-redonda"),
        ("sessao_trabalhos", "Sessão de trabalhos"),
        ("minicurso", "Minicurso / oficina"),
        ("intervalo", "Intervalo"),
        ("outro", "Outro"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evento = models.ForeignKey(EventoAcademico, on_delete=models.CASCADE, related_name="programacao")
    titulo = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="palestra")
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    sala = models.CharField(max_length=120, blank=True, default="")
    responsaveis = models.CharField(
        max_length=500, blank=True, default="", help_text="Palestrantes, mediadores ou coordenadores"
    )
    descricao = models.TextField(blank=True, default="")
    link_transmissao = models.URLField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Atividade da programação"
        verbose_name_plural = "Programação"
        ordering = ["inicio", "sala", "titulo"]
        indexes = [models.Index(fields=["evento", "inicio"])]

    def __str__(self):
        return f"{self.titulo} — {self.evento.titulo}"


class CertificadoPapel(models.Model):
    """Certificado por papel no evento além da participação: autor de trabalho aceito, parecerista."""

    AUTOR = "autor"
    PARECERISTA = "parecerista"
    PAPEL_CHOICES = [(AUTOR, "Autor(a)"), (PARECERISTA, "Parecerista")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evento = models.ForeignKey(EventoAcademico, on_delete=models.CASCADE, related_name="certificados_papel")
    papel = models.CharField(max_length=20, choices=PAPEL_CHOICES)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="certificados_papel"
    )
    submissao = models.ForeignKey(
        SubmissaoTrabalho, on_delete=models.CASCADE, null=True, blank=True, related_name="certificados"
    )
    nome = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    detalhe = models.CharField(max_length=500, blank=True, default="")
    codigo = models.CharField(max_length=16, unique=True)
    emitido_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Certificado por papel"
        verbose_name_plural = "Certificados por papel"
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "papel", "usuario", "submissao"], name="unique_certificado_papel"
            )
        ]

    def __str__(self):
        return f"{self.get_papel_display()} — {self.nome} — {self.evento.titulo}"
