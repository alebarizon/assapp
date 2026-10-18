"""API REST — Membros, Filiação e Anuidades (Sprint 4)."""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import connection
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from core.emails import nome_associacao
from django_tenants.utils import schema_context
from tenants.resolvers import resolve_tenant_from_request
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
    enviar_lembretes_anuidade,
    gerar_anuidades_ano,
    registrar_pagamento,
    resolver_membro_do_user,
    resumo_quadro,
    vincular_user,
)
from .carteirinha import build_carteirinha_pdf, dados_carteirinha, renovar_codigo, situacao
from .timeline import timeline_membro


def _carteirinha_pdf_response(membro, request):
    pdf = build_carteirinha_pdf(membro, connection.schema_name, nome_associacao(request))
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="carteirinha-{membro.matricula:06d}.pdf"'
    return response


class MembroViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "membros"

    def get_queryset(self):
        qs = Membro.objects.select_related("user").prefetch_related("filiacoes__anuidades__lembretes")

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

    @action(detail=True, methods=["get"])
    def carteirinha(self, request, pk=None):
        return Response(dados_carteirinha(self.get_object(), connection.schema_name, nome_associacao(request)))

    @action(detail=True, methods=["get"], url_path="carteirinha/pdf")
    def carteirinha_pdf(self, request, pk=None):
        return _carteirinha_pdf_response(self.get_object(), request)

    @action(detail=True, methods=["post"], url_path="carteirinha/renovar")
    def carteirinha_renovar(self, request, pk=None):
        """Gera novo QR; carteirinhas impressas ou salvas com o código anterior deixam de validar."""
        membro = renovar_codigo(self.get_object())
        return Response(dados_carteirinha(membro, connection.schema_name, nome_associacao(request)))

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        """Histórico do associado em todos os módulos (mais recente primeiro)."""
        return Response(timeline_membro(self.get_object()))


class FiliacaoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "membros"
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
    modulo = ("membros", "financeiro")
    serializer_class = AnuidadeSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = Anuidade.objects.select_related("filiacao__membro").prefetch_related("lembretes")
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

    @action(detail=False, methods=["post"])
    def enviar_lembretes(self, request):
        """Roda a régua agora (a mesma do cron diário); não repete lembretes já enviados."""
        atualizar_anuidades_vencidas()
        return Response(enviar_lembretes_anuidade(request=request))

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
            .prefetch_related("filiacoes__anuidades__lembretes")
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
            .prefetch_related("lembretes")
            .order_by("-ano_referencia", "-vencimento")
        )
        return Response(AnuidadeSerializer(qs, many=True).data)


def _meu_membro(request):
    membro = resolver_membro_do_user(request.user, auto_link=True)
    if not membro:
        raise NotFound("Nenhum associado vinculado a este usuário.")
    return membro


class MinhaCarteirinhaView(APIView):
    """GET /api/membros/meu/carteirinha/ — dados e QR da carteirinha do associado logado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(dados_carteirinha(_meu_membro(request), connection.schema_name, nome_associacao(request)))


class MinhaCarteirinhaPdfView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return _carteirinha_pdf_response(_meu_membro(request), request)


class VerificarCarteirinhaView(APIView):
    """GET /api/membros/public/carteirinha/<codigo>/?schema= — verificação pública pelo QR.

    Expõe só o necessário para conferir a filiação (sem e-mail, CPF ou contato).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, codigo):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            raise NotFound("Associação não encontrada. Informe ?schema=.")
        with schema_context(tenant.schema_name):
            membro = Membro.objects.filter(carteirinha_codigo=codigo).first()
            if not membro:
                raise NotFound("Carteirinha não encontrada ou substituída por uma mais recente.")
            return Response(
                {
                    "nome": membro.nome_completo,
                    "matricula": f"{membro.matricula:06d}" if membro.matricula else "",
                    "associacao": tenant.name,
                    "verificado_em": timezone.now(),
                    **situacao(membro),
                }
            )
