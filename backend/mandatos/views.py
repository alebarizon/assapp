"""
API REST — Mandatos (PIPE core: H1 + H2)

Endpoints principais:
- CRUD de mandatos
- Mandato ativo
- Transição entre mandatos + onboarding
- Snapshots auditáveis
"""
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Mandato, MandatoStatus, OnboardingEtapa, TransicaoMandato
from .permissions import IsBoardOrAdmin
from .serializers import (
    CargoMandatoSerializer,
    ConcluirEtapaSerializer,
    IniciarTransicaoSerializer,
    MandatoCreateUpdateSerializer,
    MandatoDetailSerializer,
    MandatoListSerializer,
    MandatoSnapshotSerializer,
    OnboardingEtapaSerializer,
    TransicaoMandatoSerializer,
)


class MandatoViewSet(viewsets.ModelViewSet):
    """
    H1 — Gestão de mandatos com histórico auditável.
    H2 — Onboarding via ações de transição.
    """
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]

    def get_queryset(self):
        return Mandato.objects.prefetch_related("cargos", "snapshots").order_by(
            "-numero_sequencial"
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MandatoDetailSerializer
        if self.action in ("update", "partial_update", "create"):
            return MandatoCreateUpdateSerializer
        return MandatoListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mandato = serializer.save()
        return Response(
            MandatoListSerializer(mandato).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def ativo(self, request):
        """Retorna o mandato ativo da associação."""
        mandato = Mandato.get_ativo()
        if not mandato:
            return Response({"detail": "Nenhum mandato ativo."}, status=status.HTTP_404_NOT_FOUND)
        return Response(MandatoDetailSerializer(mandato).data)

    @action(detail=True, methods=["post"])
    def ativar(self, request, pk=None):
        """Ativa um mandato (encerra outros ativos)."""
        mandato = self.get_object()
        if mandato.status == MandatoStatus.ENCERRADO:
            return Response(
                {"detail": "Mandato encerrado não pode ser reativado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mandato.ativar()
        return Response(MandatoDetailSerializer(mandato).data)

    @action(detail=True, methods=["post"])
    def encerrar(self, request, pk=None):
        """H1 — Encerra mandato com snapshot automático."""
        mandato = self.get_object()
        observacoes = request.data.get("observacoes", "")
        mandato.encerrar(observacoes=observacoes, criado_por=request.user)
        return Response(MandatoDetailSerializer(mandato).data)

    @action(detail=True, methods=["post"])
    def transicao(self, request, pk=None):
        """
        H1+H2 — Inicia transição para novo mandato.
        Cria snapshot, TransicaoMandato e etapas de onboarding.
        """
        mandato_anterior = self.get_object()
        serializer = IniciarTransicaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mandato_novo = get_object_or_404(
            Mandato, pk=serializer.validated_data["mandato_novo_id"]
        )

        if mandato_anterior.id == mandato_novo.id:
            return Response(
                {"detail": "Mandato anterior e novo devem ser diferentes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transicao = mandato_anterior.iniciar_transicao(mandato_novo)
        if serializer.validated_data.get("notas_transicao"):
            transicao.notas_transicao = serializer.validated_data["notas_transicao"]
            transicao.save(update_fields=["notas_transicao"])

        return Response(
            TransicaoMandatoSerializer(transicao).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def snapshots(self, request, pk=None):
        """Lista snapshots do mandato (H1 — auditoria)."""
        mandato = self.get_object()
        snapshots = mandato.snapshots.all()
        return Response(MandatoSnapshotSerializer(snapshots, many=True).data)

    @action(detail=True, methods=["post"])
    def snapshot_manual(self, request, pk=None):
        """Cria snapshot manual do mandato."""
        mandato = self.get_object()
        snapshot = mandato.criar_snapshot(tipo="manual", criado_por=request.user)
        return Response(
            MandatoSnapshotSerializer(snapshot).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get", "post"])
    def cargos(self, request, pk=None):
        """Lista ou adiciona cargos da diretoria."""
        mandato = self.get_object()
        if request.method == "GET":
            cargos = mandato.cargos.select_related("usuario").all()
            return Response(CargoMandatoSerializer(cargos, many=True).data)

        data = request.data.copy()
        data["mandato"] = str(mandato.id)
        serializer = CargoMandatoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TransicaoMandatoViewSet(viewsets.ReadOnlyModelViewSet):
    """Consulta transições de mandato em andamento ou concluídas."""
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    serializer_class = TransicaoMandatoSerializer

    def get_queryset(self):
        return TransicaoMandato.objects.select_related(
            "mandato_anterior", "mandato_novo"
        ).prefetch_related("etapas_onboarding")

    @action(detail=False, methods=["get"])
    def em_andamento(self, request):
        """Retorna transição ativa (para modo Nova Diretoria — H2)."""
        transicao = (
            self.get_queryset()
            .exclude(status="concluida")
            .exclude(status="cancelada")
            .order_by("-data_inicio_transicao")
            .first()
        )
        if not transicao:
            return Response({"detail": "Nenhuma transição em andamento."}, status=404)
        return Response(TransicaoMandatoSerializer(transicao).data)


class OnboardingEtapaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    H2 — Etapas do wizard de onboarding.
    Filtra por perfil técnico do usuário autenticado.
    """
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    serializer_class = OnboardingEtapaSerializer

    def get_queryset(self):
        qs = OnboardingEtapa.objects.select_related("transicao", "responsavel")
        perfil = getattr(self.request.user, "perfil_tecnico", "iniciante")
        # H2: retorna todas, mas marca visibilidade no serializer via action
        return qs.order_by("ordem")

    def list(self, request, *args, **kwargs):
        transicao_id = request.query_params.get("transicao")
        if not transicao_id:
            return Response(
                {"detail": "Parâmetro 'transicao' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(transicao_id=transicao_id)
        perfil = getattr(request.user, "perfil_tecnico", "iniciante")

        data = []
        for etapa in qs:
            item = OnboardingEtapaSerializer(etapa).data
            item["visivel"] = etapa.visivel_para_perfil(perfil)
            data.append(item)

        return Response(data)

    @action(detail=True, methods=["post"])
    def concluir(self, request, pk=None):
        """Marca etapa como concluída e atualiza progresso da transição."""
        etapa = self.get_object()
        serializer = ConcluirEtapaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get("dados_contexto"):
            etapa.dados_contexto = {
                **(etapa.dados_contexto or {}),
                **serializer.validated_data["dados_contexto"],
            }
            etapa.save(update_fields=["dados_contexto"])

        etapa.marcar_concluida(responsavel=request.user)
        return Response(OnboardingEtapaSerializer(etapa).data)
