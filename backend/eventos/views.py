"""API REST — Eventos Acadêmicos (H3)."""
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from mandatos.permissions import IsBoardOrAdmin
from membros.models import Membro

from .models import (
    CallForPapers,
    EventoAcademico,
    InscricaoEvento,
    Parecer,
    SubmissaoTrabalho,
)
from .serializers import (
    AbrirCfpSerializer,
    AtribuirPareceristaSerializer,
    CallForPapersSerializer,
    ConcluirParecerSerializer,
    EventoCreateSerializer,
    EventoDetailSerializer,
    EventoListSerializer,
    GerarAnaisSerializer,
    InscricaoEventoSerializer,
    ParecerSerializer,
    SubmissaoCreateSerializer,
    SubmissaoTrabalhoSerializer,
)
from .services import (
    abrir_cfp,
    atribuir_parecerista,
    concluir_parecer,
    criar_evento_com_mandato,
    gerar_anais,
    resumo_eventos,
    submeter_trabalho,
)


class EventoAcademicoViewSet(viewsets.ModelViewSet):
    """H3 — Eventos científicos integrados a membros e mandatos."""
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]

    def get_queryset(self):
        return EventoAcademico.objects.select_related(
            "mandato", "call_for_papers", "anais"
        ).order_by("-data_inicio")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EventoDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return EventoCreateSerializer
        return EventoListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evento = criar_evento_com_mandato(serializer.validated_data)
        return Response(EventoListSerializer(evento).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def resumo(self, request):
        return Response(resumo_eventos())

    @action(detail=True, methods=["post"])
    def abrir_cfp(self, request, pk=None):
        evento = self.get_object()
        serializer = AbrirCfpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cfp = abrir_cfp(evento, serializer.validated_data)
        return Response(CallForPapersSerializer(cfp).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def gerar_anais(self, request, pk=None):
        """H3 — publica anais a partir de submissões aceitas."""
        evento = self.get_object()
        serializer = GerarAnaisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            anais = gerar_anais(
                evento,
                titulo=serializer.validated_data.get("titulo"),
                issn=serializer.validated_data.get("issn"),
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        from .serializers import AnaisPublicacaoSerializer
        return Response(AnaisPublicacaoSerializer(anais).data)

    @action(detail=True, methods=["get"])
    def submissoes(self, request, pk=None):
        evento = self.get_object()
        if not hasattr(evento, "call_for_papers"):
            return Response([])
        qs = evento.call_for_papers.submissoes.select_related(
            "autor", "membro"
        ).prefetch_related("pareceres")
        return Response(SubmissaoTrabalhoSerializer(qs, many=True).data)


class SubmissaoTrabalhoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return SubmissaoTrabalho.objects.select_related(
            "cfp", "autor", "membro"
        ).prefetch_related("pareceres")

    def get_serializer_class(self):
        if self.action == "create":
            return SubmissaoCreateSerializer
        return SubmissaoTrabalhoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data.copy()
        membro_id = dados.pop("membro_id", None)

        submissao = SubmissaoTrabalho.objects.create(
            autor=request.user,
            **dados,
        )
        if membro_id:
            submissao.membro = get_object_or_404(Membro, pk=membro_id)
            submissao.save(update_fields=["membro"])

        return Response(
            SubmissaoTrabalhoSerializer(submissao).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def submeter(self, request, pk=None):
        submissao = self.get_object()
        submissao = submeter_trabalho(submissao)
        return Response(SubmissaoTrabalhoSerializer(submissao).data)

    @action(detail=True, methods=["post"])
    def atribuir_parecerista(self, request, pk=None):
        submissao = self.get_object()
        serializer = AtribuirPareceristaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parecerista = get_object_or_404(
            User, pk=serializer.validated_data["parecerista_id"]
        )
        parecer = atribuir_parecerista(submissao, parecerista)
        return Response(ParecerSerializer(parecer).data, status=status.HTTP_201_CREATED)


class ParecerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    serializer_class = ParecerSerializer

    def get_queryset(self):
        return Parecer.objects.select_related("submissao", "parecerista")

    @action(detail=True, methods=["post"])
    def concluir(self, request, pk=None):
        parecer = self.get_object()
        serializer = ConcluirParecerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parecer = concluir_parecer(parecer, **serializer.validated_data)
        return Response(ParecerSerializer(parecer).data)


class InscricaoEventoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    serializer_class = InscricaoEventoSerializer

    def get_queryset(self):
        qs = InscricaoEvento.objects.select_related("evento", "membro")
        evento_id = self.request.query_params.get("evento")
        if evento_id:
            qs = qs.filter(evento_id=evento_id)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        membro_id = self.request.data.get("membro")
        save_kwargs = {}
        if membro_id:
            membro = Membro.objects.filter(pk=membro_id).first()
            if membro:
                save_kwargs["membro"] = membro
                if not serializer.validated_data.get("nome"):
                    save_kwargs["nome"] = membro.nome_completo
                if not serializer.validated_data.get("email"):
                    save_kwargs["email"] = membro.email
        serializer.save(**save_kwargs)
