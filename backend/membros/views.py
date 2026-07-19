"""API REST — Membros, Filiação e Anuidades (Sprint 4)."""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from mandatos.models import Mandato
from mandatos.permissions import IsBoardOrAdmin

from .models import Anuidade, Filiacao, Membro
from .serializers import (
    AnuidadeSerializer,
    FiliacaoSerializer,
    GerarAnuidadesSerializer,
    MembroCreateSerializer,
    MembroDetailSerializer,
    MembroListSerializer,
    RegistrarPagamentoSerializer,
    VincularUserSerializer,
)
from .services import (
    atualizar_anuidades_vencidas,
    criar_membro_com_filiacao,
    desvincular_user,
    gerar_anuidades_ano,
    registrar_pagamento,
    resolver_membro_do_user,
    resumo_quadro,
    vincular_user,
)


class MembroViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]

    def get_queryset(self):
        qs = Membro.objects.select_related("user").prefetch_related("filiacoes__anuidades")

        status_filiacao = self.request.query_params.get("status_filiacao")
        if status_filiacao:
            qs = qs.filter(filiacoes__status=status_filiacao, filiacoes__data_fim__isnull=True)

        busca = self.request.query_params.get("q")
        if busca:
            qs = qs.filter(
                Q(nome_completo__icontains=busca)
                | Q(email__icontains=busca)
                | Q(cpf__icontains=busca)
                | Q(instituicao__icontains=busca)
            )

        ativo = self.request.query_params.get("ativo")
        if ativo is not None:
            qs = qs.filter(ativo=ativo.lower() == "true")

        return qs.distinct().order_by("nome_completo")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MembroDetailSerializer
        if self.action == "create":
            return MembroCreateSerializer
        return MembroListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data.copy()
        tipo_filiacao = dados.pop("tipo_filiacao", "efetivo")

        if dados.get("consentimento_lgpd"):
            dados["consentimento_em"] = timezone.now()

        mandato = Mandato.get_ativo()
        membro, filiacao = criar_membro_com_filiacao(
            dados_membro=dados,
            tipo_filiacao=tipo_filiacao,
            mandato=mandato,
        )
        return Response(
            MembroDetailSerializer(membro).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def resumo(self, request):
        """KPIs do quadro de associados."""
        return Response(resumo_quadro())

    @action(detail=True, methods=["post"])
    def vincular_user(self, request, pk=None):
        """Liga User ao Membro (user_id ou email)."""
        membro = self.get_object()
        serializer = VincularUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data.get("user_id"):
            user = User.objects.filter(id=data["user_id"]).first()
        else:
            user = User.objects.filter(email__iexact=data["email"]).first()
        if not user:
            return Response(
                {"detail": "Usuário não encontrado neste tenant."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            membro = vincular_user(membro, user)
        except DjangoValidationError as e:
            detail = e.message_dict if hasattr(e, "message_dict") else e.messages
            return Response(detail, status=status.HTTP_400_BAD_REQUEST)
        return Response(MembroDetailSerializer(membro).data)

    @action(detail=True, methods=["post"])
    def desvincular_user(self, request, pk=None):
        membro = desvincular_user(self.get_object())
        return Response(MembroDetailSerializer(membro).data)


class FiliacaoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    serializer_class = FiliacaoSerializer

    def get_queryset(self):
        qs = Filiacao.objects.select_related("membro", "mandato").prefetch_related("anuidades")
        membro_id = self.request.query_params.get("membro")
        if membro_id:
            qs = qs.filter(membro_id=membro_id)
        return qs.order_by("-data_inicio")

    def perform_create(self, serializer):
        mandato = Mandato.get_ativo()
        serializer.save(mandato=mandato)


class AnuidadeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    serializer_class = AnuidadeSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = Anuidade.objects.select_related("filiacao__membro")
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        ano = self.request.query_params.get("ano")
        if ano:
            qs = qs.filter(ano_referencia=ano)
        return qs.order_by("-ano_referencia", "filiacao__membro__nome_completo")

    @action(detail=False, methods=["post"])
    def gerar_lote(self, request):
        """Gera anuidades em lote para filiações ativas."""
        serializer = GerarAnuidadesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = gerar_anuidades_ano(
            ano=serializer.validated_data["ano"],
            valor=serializer.validated_data.get("valor"),
            vencimento=serializer.validated_data.get("vencimento"),
            mandato=Mandato.get_ativo(),
        )
        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def atualizar_vencidas(self, request):
        """Atualiza status de anuidades vencidas e filiações inadimplentes."""
        result = atualizar_anuidades_vencidas()
        return Response(result)

    @action(detail=True, methods=["post"])
    def registrar_pagamento(self, request, pk=None):
        anuidade = self.get_object()
        serializer = RegistrarPagamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        anuidade = registrar_pagamento(
            anuidade,
            nf_numero=serializer.validated_data.get("nf_numero"),
            user=request.user,
        )
        return Response(AnuidadeSerializer(anuidade).data)


class MeuMembroView(APIView):
    """Perfil do associado vinculado ao User autenticado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        membro = resolver_membro_do_user(request.user, auto_link=True)
        if not membro:
            return Response(
                {"detail": "Nenhum associado vinculado a este usuário."},
                status=status.HTTP_404_NOT_FOUND,
            )
        membro = (
            Membro.objects.filter(pk=membro.pk)
            .select_related("user")
            .prefetch_related("filiacoes__anuidades")
            .first()
        )
        return Response(MembroDetailSerializer(membro).data)


class MinhasAnuidadesView(APIView):
    """Anuidades do próprio Membro (read-only)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        membro = resolver_membro_do_user(request.user, auto_link=True)
        if not membro:
            return Response(
                {"detail": "Nenhum associado vinculado a este usuário."},
                status=status.HTTP_404_NOT_FOUND,
            )
        qs = (
            Anuidade.objects.filter(filiacao__membro=membro)
            .select_related("filiacao__membro")
            .order_by("-ano_referencia", "-vencimento")
        )
        return Response(AnuidadeSerializer(qs, many=True).data)
