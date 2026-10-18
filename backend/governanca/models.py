"""Assembleias e votações (eleições e deliberações) da associação."""
import uuid

from django.conf import settings
from django.db import models


class TipoAssembleia(models.TextChoices):
    ORDINARIA = "ordinaria", "Ordinária"
    EXTRAORDINARIA = "extraordinaria", "Extraordinária"


class Modalidade(models.TextChoices):
    PRESENCIAL = "presencial", "Presencial"
    ONLINE = "online", "Online"
    HIBRIDA = "hibrida", "Híbrida"


class AssembleiaStatus(models.TextChoices):
    RASCUNHO = "rascunho", "Rascunho"
    CONVOCADA = "convocada", "Convocada"
    EM_ANDAMENTO = "em_andamento", "Em andamento"
    ENCERRADA = "encerrada", "Encerrada"
    CANCELADA = "cancelada", "Cancelada"


class Assembleia(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TipoAssembleia.choices, default=TipoAssembleia.ORDINARIA)
    data_hora = models.DateTimeField()
    modalidade = models.CharField(max_length=20, choices=Modalidade.choices, default=Modalidade.PRESENCIAL)
    local = models.CharField(max_length=255, blank=True)
    link_online = models.URLField(blank=True)
    convocacao = models.TextField(blank=True, help_text="Texto do edital de convocação")
    pauta = models.JSONField(default=list, blank=True, help_text="Lista de itens da ordem do dia")
    quorum_minimo = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Percentual mínimo de aptos presentes; vazio = sem quórum"
    )
    status = models.CharField(
        max_length=20, choices=AssembleiaStatus.choices, default=AssembleiaStatus.RASCUNHO, db_index=True
    )
    mandato = models.ForeignKey(
        "mandatos.Mandato", on_delete=models.SET_NULL, null=True, blank=True, related_name="assembleias"
    )
    convocada_em = models.DateTimeField(null=True, blank=True)
    encerrada_em = models.DateTimeField(null=True, blank=True)
    ata = models.TextField(blank=True)
    ata_publicada_em = models.DateTimeField(null=True, blank=True)
    ata_hash = models.CharField(max_length=64, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Assembleia"
        verbose_name_plural = "Assembleias"
        ordering = ["-data_hora"]

    def __str__(self):
        return self.titulo


class FormaPresenca(models.TextChoices):
    PRESENCIAL = "presencial", "Presencial"
    ONLINE = "online", "Online"


class PresencaAssembleia(models.Model):
    assembleia = models.ForeignKey(Assembleia, on_delete=models.CASCADE, related_name="presencas")
    membro = models.ForeignKey("membros.Membro", on_delete=models.CASCADE, related_name="presencas_assembleia")
    forma = models.CharField(max_length=20, choices=FormaPresenca.choices, default=FormaPresenca.PRESENCIAL)
    registrada_em = models.DateTimeField(auto_now_add=True)
    registrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        verbose_name = "Presença em assembleia"
        verbose_name_plural = "Presenças em assembleia"
        ordering = ["membro__nome_completo"]
        constraints = [models.UniqueConstraint(fields=["assembleia", "membro"], name="presenca_unica_assembleia")]


class TipoVotacao(models.TextChoices):
    ELEICAO = "eleicao", "Eleição"
    DELIBERACAO = "deliberacao", "Deliberação"


class VotacaoStatus(models.TextChoices):
    RASCUNHO = "rascunho", "Rascunho"
    ABERTA = "aberta", "Aberta"
    ENCERRADA = "encerrada", "Encerrada"
    CANCELADA = "cancelada", "Cancelada"


class CensoVotacao(models.TextChoices):
    ADIMPLENTES = "adimplentes", "Associados em dia"
    ATIVOS = "ativos", "Todos os associados ativos"


class Votacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assembleia = models.ForeignKey(
        Assembleia, on_delete=models.SET_NULL, null=True, blank=True, related_name="votacoes"
    )
    mandato = models.ForeignKey(
        "mandatos.Mandato", on_delete=models.SET_NULL, null=True, blank=True, related_name="votacoes"
    )
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TipoVotacao.choices, default=TipoVotacao.DELIBERACAO)
    status = models.CharField(
        max_length=20, choices=VotacaoStatus.choices, default=VotacaoStatus.RASCUNHO, db_index=True
    )
    censo = models.CharField(max_length=20, choices=CensoVotacao.choices, default=CensoVotacao.ADIMPLENTES)
    secreta = models.BooleanField(default=True)
    max_escolhas = models.PositiveSmallIntegerField(default=1)
    permite_branco = models.BooleanField(default=True)
    fecha_em = models.DateTimeField(null=True, blank=True, help_text="Prazo para votar; vazio = até encerrar")
    aberta_em = models.DateTimeField(null=True, blank=True)
    encerrada_em = models.DateTimeField(null=True, blank=True)
    resultado = models.JSONField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Votação"
        verbose_name_plural = "Votações"
        ordering = ["-created_at"]

    def __str__(self):
        return self.titulo


class OpcaoVotacao(models.Model):
    votacao = models.ForeignKey(Votacao, on_delete=models.CASCADE, related_name="opcoes")
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    integrantes = models.JSONField(default=list, blank=True, help_text='Chapa: [{"nome", "cargo"}]')
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Opção de votação"
        verbose_name_plural = "Opções de votação"
        ordering = ["ordem", "id"]

    def __str__(self):
        return self.titulo


class Eleitor(models.Model):
    """Censo congelado na abertura da votação."""

    votacao = models.ForeignKey(Votacao, on_delete=models.CASCADE, related_name="eleitores")
    membro = models.ForeignKey("membros.Membro", on_delete=models.CASCADE, related_name="participacoes_votacao")
    votou_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Eleitor"
        verbose_name_plural = "Eleitores"
        constraints = [models.UniqueConstraint(fields=["votacao", "membro"], name="eleitor_unico_votacao")]


class Cedula(models.Model):
    """Voto depositado. Em votação secreta não guarda quem votou; sem opções = voto em branco."""

    # UUID e só a data: nem a ordem de inserção nem o horário permitem cruzar a cédula com Eleitor.votou_em.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    votacao = models.ForeignKey(Votacao, on_delete=models.CASCADE, related_name="cedulas")
    opcoes = models.ManyToManyField(OpcaoVotacao, blank=True, related_name="cedulas")
    eleitor = models.OneToOneField(Eleitor, on_delete=models.SET_NULL, null=True, blank=True, related_name="cedula")
    comprovante = models.CharField(max_length=16, unique=True)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Cédula"
        verbose_name_plural = "Cédulas"
