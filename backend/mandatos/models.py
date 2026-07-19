"""
AssApp — Módulo Mandatos (PIPE Fase 1 — Prioridade Máxima)

Hipótese H1: Modelagem de conhecimento institucional com histórico auditável.
Hipótese H2: Onboarding guiado adaptativo para nova diretoria.

Este módulo implementa:
- Ciclo de vida do Mandato (planejado → ativo → transição → encerrado)
- Cargos da diretoria vinculados a usuários
- Transição estruturada entre mandatos com wizard de onboarding
- Snapshot automático ao encerrar mandato
"""
import hashlib
import json
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class MandatoStatus(models.TextChoices):
    PLANEJADO = "planejado", "Planejado"
    ATIVO = "ativo", "Ativo"
    TRANSICAO = "transicao", "Em Transição"
    ENCERRADO = "encerrado", "Encerrado"
    ARQUIVADO = "arquivado", "Arquivado"


class TipoCargo(models.TextChoices):
    PRESIDENTE = "presidente", "Presidente"
    VICE_PRESIDENTE = "vice_presidente", "Vice-Presidente"
    SECRETARIO = "secretario", "Secretário"
    SECRETARIO_ADJUNTO = "secretario_adjunto", "Secretário Adjunto"
    TESOUREIRO = "tesoureiro", "Tesoureiro"
    TESOUREIRO_ADJUNTO = "tesoureiro_adjunto", "Tesoureiro Adjunto"
    DIRETOR = "diretor", "Diretor"
    CONSELHO_FISCAL = "conselho_fiscal", "Conselho Fiscal"
    OUTRO = "outro", "Outro"


class TransicaoStatus(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    EM_ANDAMENTO = "em_andamento", "Em Andamento"
    ONBOARDING_PARCIAL = "onboarding_parcial", "Onboarding Parcial"
    CONCLUIDA = "concluida", "Concluída"
    CANCELADA = "cancelada", "Cancelada"


class PerfilTecnico(models.TextChoices):
    """H2 — perfil para adaptação de interface."""
    INICIANTE = "iniciante", "Iniciante"
    INTERMEDIARIO = "intermediario", "Intermediário"
    AVANCADO = "avancado", "Avançado"


# Etapas padrão do wizard de onboarding (H1 + H2)
ETAPAS_ONBOARDING_PADRAO = [
    {
        "codigo": "revisar_snapshot",
        "titulo": "Revisar snapshot do mandato anterior",
        "descricao": "Conheça o estado consolidado da gestão anterior: membros, finanças e eventos.",
        "ordem": 1,
        "obrigatoria": True,
        "perfil_minimo": PerfilTecnico.INICIANTE,
    },
    {
        "codigo": "confirmar_diretoria",
        "titulo": "Confirmar composição da nova diretoria",
        "descricao": "Valide os cargos e responsáveis do mandato atual.",
        "ordem": 2,
        "obrigatoria": True,
        "perfil_minimo": PerfilTecnico.INICIANTE,
    },
    {
        "codigo": "revisar_membros",
        "titulo": "Revisar quadro de associados",
        "descricao": "Verifique filiações ativas, inadimplências e renovações pendentes.",
        "ordem": 3,
        "obrigatoria": True,
        "perfil_minimo": PerfilTecnico.INICIANTE,
    },
    {
        "codigo": "revisar_financeiro",
        "titulo": "Revisar situação financeira",
        "descricao": "Consulte saldo, receitas de anuidades e despesas recorrentes.",
        "ordem": 4,
        "obrigatoria": True,
        "perfil_minimo": PerfilTecnico.INTERMEDIARIO,
    },
    {
        "codigo": "revisar_eventos",
        "titulo": "Revisar eventos em andamento",
        "descricao": "Verifique CFPs abertos, submissões pendentes e inscrições.",
        "ordem": 5,
        "obrigatoria": False,
        "perfil_minimo": PerfilTecnico.INTERMEDIARIO,
    },
    {
        "codigo": "revisar_decisoes",
        "titulo": "Revisar decisões institucionais",
        "descricao": "Leia as principais decisões e contextos do mandato anterior.",
        "ordem": 6,
        "obrigatoria": True,
        "perfil_minimo": PerfilTecnico.INICIANTE,
    },
    {
        "codigo": "configurar_comunicacao",
        "titulo": "Configurar canais de comunicação",
        "descricao": "Atualize listas de e-mail, templates e integrações.",
        "ordem": 7,
        "obrigatoria": False,
        "perfil_minimo": PerfilTecnico.AVANCADO,
    },
]


class Mandato(models.Model):
    """
    Ciclo de gestão da diretoria (~2 anos).
    Entidade central da hipótese H1.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=255, help_text="Ex: Diretoria 2024-2026")
    descricao = models.TextField(blank=True, null=True)
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=MandatoStatus.choices,
        default=MandatoStatus.PLANEJADO,
        db_index=True,
    )
    numero_sequencial = models.PositiveIntegerField(
        help_text="Número sequencial do mandato na associação (1, 2, 3...)"
    )
    observacoes_encerramento = models.TextField(blank=True, null=True)
    encerrado_em = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mandato"
        verbose_name_plural = "Mandatos"
        ordering = ["-numero_sequencial"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["data_inicio", "data_fim"]),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.get_status_display()})"

    @classmethod
    def get_ativo(cls):
        """Retorna o mandato ativo da associação, se existir."""
        return cls.objects.filter(status=MandatoStatus.ATIVO).first()

    def ativar(self):
        """Ativa este mandato, encerrando qualquer outro ativo."""
        Mandato.objects.filter(status=MandatoStatus.ATIVO).exclude(pk=self.pk).update(
            status=MandatoStatus.ENCERRADO,
            encerrado_em=timezone.now(),
        )
        self.status = MandatoStatus.ATIVO
        self.save(update_fields=["status", "updated_at"])

    def iniciar_transicao(self, mandato_novo: "Mandato") -> "TransicaoMandato":
        """
        Inicia transição para um novo mandato.
        Cria snapshot do mandato atual e etapas de onboarding (H1 + H2).
        """
        self.status = MandatoStatus.TRANSICAO
        self.save(update_fields=["status", "updated_at"])

        snapshot = self.criar_snapshot(tipo="transicao")

        transicao = TransicaoMandato.objects.create(
            mandato_anterior=self,
            mandato_novo=mandato_novo,
            status=TransicaoStatus.EM_ANDAMENTO,
        )

        for etapa in ETAPAS_ONBOARDING_PADRAO:
            OnboardingEtapa.objects.create(
                transicao=transicao,
                codigo=etapa["codigo"],
                titulo=etapa["titulo"],
                descricao=etapa["descricao"],
                ordem=etapa["ordem"],
                obrigatoria=etapa["obrigatoria"],
                perfil_minimo=etapa["perfil_minimo"],
                dados_contexto={"snapshot_id": str(snapshot.id)},
            )

        return transicao

    def criar_snapshot(self, tipo: str = "encerramento", criado_por=None) -> "MandatoSnapshot":
        """
        H1 — Snapshot automático com estado consolidado.
        Captura: cargos, contagens de membros, resumo financeiro, eventos ativos.
        """
        dados = {
            "mandato": {
                "id": str(self.id),
                "titulo": self.titulo,
                "data_inicio": self.data_inicio.isoformat(),
                "data_fim": self.data_fim.isoformat() if self.data_fim else None,
                "numero_sequencial": self.numero_sequencial,
            },
            "cargos": [
                {
                    "usuario_id": str(c.usuario_id),
                    "cargo": c.cargo,
                    "cargo_custom": c.cargo_custom,
                }
                for c in self.cargos.filter(ativo=True)
            ],
            "capturado_em": timezone.now().isoformat(),
        }

        # Integrações lazy para evitar import circular
        try:
            from membros.models import Filiacao, FiliacaoStatus
            dados["membros"] = {
                "ativos": Filiacao.objects.filter(status=FiliacaoStatus.ATIVA).count(),
                "inadimplentes": Filiacao.objects.filter(
                    status=FiliacaoStatus.INADIMPLENTE
                ).count(),
            }
        except Exception:
            dados["membros"] = {"ativos": 0, "inadimplentes": 0}

        try:
            from memoria.models import ContextoHistorico
            dados["decisoes_recentes"] = list(
                ContextoHistorico.objects.filter(mandato=self, arquivado=False)
                .order_by("-created_at")[:10]
                .values("id", "titulo", "decisao", "created_at")
            )
        except Exception:
            dados["decisoes_recentes"] = []

        # Resumo anuidades (H1 — transição)
        try:
            from membros.models import Anuidade, AnuidadeStatus
            dados["anuidades"] = {
                "pagas": Anuidade.objects.filter(status=AnuidadeStatus.PAGA).count(),
                "pendentes": Anuidade.objects.filter(status=AnuidadeStatus.PENDENTE).count(),
                "vencidas": Anuidade.objects.filter(status=AnuidadeStatus.VENCIDA).count(),
            }
        except Exception:
            dados["anuidades"] = {"pagas": 0, "pendentes": 0, "vencidas": 0}

        # Saldo do mês corrente (finance OSC)
        try:
            from decimal import Decimal
            from django.db.models import Sum
            from finance.models import Transaction, TransactionType

            hoje = timezone.now()
            qs = Transaction.objects.filter(
                occurred_at__year=hoje.year,
                occurred_at__month=hoje.month,
            )
            income = qs.filter(type=TransactionType.INCOME).aggregate(
                t=Sum("amount")
            )["t"] or Decimal("0")
            expense = qs.filter(type=TransactionType.EXPENSE).aggregate(
                t=Sum("amount")
            )["t"] or Decimal("0")
            dados["financeiro"] = {
                "mes": hoje.month,
                "ano": hoje.year,
                "receitas": str(income),
                "despesas": str(expense),
                "saldo": str(income - expense),
            }
        except Exception:
            dados["financeiro"] = None

        # Eventos ativos / em andamento (H1)
        try:
            from eventos.models import EventoAcademicoStatus

            status_ativos = [
                EventoAcademicoStatus.INSCRICOES_ABERTAS,
                EventoAcademicoStatus.CFP_ABERTO,
                EventoAcademicoStatus.EM_AVALIACAO,
            ]
            qs_ev = self.eventos.filter(status__in=status_ativos)
            dados["eventos"] = {
                "ativos": qs_ev.count(),
                "itens": [
                    {
                        "id": str(e.id),
                        "titulo": e.titulo,
                        "status": e.status,
                        "slug": e.slug,
                    }
                    for e in qs_ev.order_by("data_inicio")[:20]
                ],
            }
        except Exception:
            dados["eventos"] = {"ativos": 0, "itens": []}

        dados_json = json.dumps(dados, sort_keys=True, default=str)
        hash_integridade = hashlib.sha256(dados_json.encode()).hexdigest()
        # JSONField/psycopg2 precisam de tipos JSON-nativos (UUID/datetime → str)
        dados = json.loads(dados_json)

        ultima_versao = self.snapshots.aggregate(models.Max("versao"))["versao__max"] or 0

        return MandatoSnapshot.objects.create(
            mandato=self,
            tipo=tipo,
            versao=ultima_versao + 1,
            dados=dados,
            hash=hash_integridade,
            criado_por=criado_por,
        )

    def encerrar(self, observacoes: str = None, criado_por=None):
        """Encerra o mandato com snapshot final e arquiva contextos (H1)."""
        self.criar_snapshot(tipo="encerramento", criado_por=criado_por)
        # H1 — arquivamento automático da memória institucional
        try:
            from memoria.services import arquivar_contextos_do_mandato
            arquivar_contextos_do_mandato(self)
        except Exception:
            pass
        self.status = MandatoStatus.ENCERRADO
        self.encerrado_em = timezone.now()
        if observacoes:
            self.observacoes_encerramento = observacoes
        self.save()


class CargoMandato(models.Model):
    """Membro da diretoria em um mandato específico."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mandato = models.ForeignKey(
        Mandato, on_delete=models.CASCADE, related_name="cargos"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cargos_mandato",
    )
    cargo = models.CharField(max_length=30, choices=TipoCargo.choices)
    cargo_custom = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Nome do cargo quando tipo = outro"
    )
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cargo no Mandato"
        verbose_name_plural = "Cargos no Mandato"
        unique_together = [["mandato", "usuario", "cargo"]]
        indexes = [models.Index(fields=["mandato", "ativo"])]

    def __str__(self):
        return f"{self.usuario} — {self.get_cargo_display()} ({self.mandato.titulo})"


class TransicaoMandato(models.Model):
    """
    Handoff estruturado entre mandatos.
    Core do onboarding guiado (H1 + H2).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mandato_anterior = models.ForeignKey(
        Mandato,
        on_delete=models.CASCADE,
        related_name="transicao_como_anterior",
    )
    mandato_novo = models.ForeignKey(
        Mandato,
        on_delete=models.CASCADE,
        related_name="transicao_como_novo",
    )
    status = models.CharField(
        max_length=25,
        choices=TransicaoStatus.choices,
        default=TransicaoStatus.PENDENTE,
    )
    data_inicio_transicao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(blank=True, null=True)
    progresso_percentual = models.PositiveSmallIntegerField(default=0)
    notas_transicao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Transição de Mandato"
        verbose_name_plural = "Transições de Mandato"
        unique_together = [["mandato_anterior", "mandato_novo"]]

    def __str__(self):
        return f"{self.mandato_anterior.titulo} → {self.mandato_novo.titulo}"

    def atualizar_progresso(self):
        """Recalcula progresso com base nas etapas obrigatórias concluídas."""
        etapas = self.etapas_onboarding.filter(obrigatoria=True)
        total = etapas.count()
        if total == 0:
            self.progresso_percentual = 100
        else:
            concluidas = etapas.filter(concluida=True).count()
            self.progresso_percentual = int((concluidas / total) * 100)

        if self.progresso_percentual == 100:
            self.status = TransicaoStatus.CONCLUIDA
            self.data_conclusao = timezone.now()
            self.mandato_novo.ativar()
            self.mandato_anterior.encerrar()
        elif self.progresso_percentual > 0:
            self.status = TransicaoStatus.ONBOARDING_PARCIAL

        self.save()

    @property
    def etapas_pendentes(self):
        return self.etapas_onboarding.filter(concluida=False, obrigatoria=True)


class OnboardingEtapa(models.Model):
    """
    Etapa do wizard de onboarding — adaptativo conforme perfil técnico (H2).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transicao = models.ForeignKey(
        TransicaoMandato,
        on_delete=models.CASCADE,
        related_name="etapas_onboarding",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarding_etapas",
    )
    codigo = models.CharField(max_length=50, db_index=True)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    ordem = models.PositiveSmallIntegerField()
    obrigatoria = models.BooleanField(default=True)
    concluida = models.BooleanField(default=False)
    concluida_em = models.DateTimeField(blank=True, null=True)
    dados_contexto = models.JSONField(blank=True, null=True)
    perfil_minimo = models.CharField(
        max_length=20,
        choices=PerfilTecnico.choices,
        default=PerfilTecnico.INICIANTE,
    )

    class Meta:
        verbose_name = "Etapa de Onboarding"
        verbose_name_plural = "Etapas de Onboarding"
        unique_together = [["transicao", "codigo"]]
        ordering = ["ordem"]
        indexes = [models.Index(fields=["transicao", "ordem"])]

    def __str__(self):
        status = "✓" if self.concluida else "○"
        return f"{status} {self.titulo}"

    def marcar_concluida(self, responsavel=None):
        self.concluida = True
        self.concluida_em = timezone.now()
        if responsavel:
            self.responsavel = responsavel
        self.save()
        self.transicao.atualizar_progresso()

    def visivel_para_perfil(self, perfil: str) -> bool:
        """H2 — filtra etapas conforme perfil técnico do usuário."""
        ordem_perfis = [p.value for p in PerfilTecnico]
        return ordem_perfis.index(perfil) >= ordem_perfis.index(self.perfil_minimo)


class MandatoSnapshot(models.Model):
    """
    H1 — Snapshot auditável do estado do mandato.
  """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mandato = models.ForeignKey(
        Mandato, on_delete=models.CASCADE, related_name="snapshots"
    )
    tipo = models.CharField(
        max_length=20,
        help_text="encerramento | transicao | manual",
    )
    versao = models.PositiveIntegerField(default=1)
    dados = models.JSONField()
    hash = models.CharField(max_length=64, blank=True, null=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="snapshots_criados",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Snapshot de Mandato"
        verbose_name_plural = "Snapshots de Mandato"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["mandato", "tipo"])]

    def __str__(self):
        return f"Snapshot v{self.versao} — {self.mandato.titulo} ({self.tipo})"

    def verificar_integridade(self) -> bool:
        """Verifica hash SHA-256 dos dados armazenados."""
        if not self.hash:
            return False
        dados_json = json.dumps(self.dados, sort_keys=True, default=str)
        return hashlib.sha256(dados_json.encode()).hexdigest() == self.hash
