"""API de pagamento online (/api/pagamentos/)."""
import hmac
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django_tenants.utils import schema_context
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.access import pode_acessar
from ecommerce.models import Order
from membros.models import Anuidade
from membros.services import resolver_membro_do_user
from tenants.resolvers import resolve_tenant_from_request

from .gateways import GatewayError
from .models import Cobranca, ConfiguracaoPagamento
from .serializers import CobrancaSerializer, CobrarSerializer, ConfiguracaoPagamentoSerializer
from .services import (
    cobrar_anuidade,
    cobrar_pedido,
    confirmar_cobranca,
    disponibilidade,
    gateway_da_config,
    processar_webhook_asaas,
    processar_webhook_mercadopago,
    processar_webhook_pagbank,
    sincronizar_cobranca,
)

logger = logging.getLogger(__name__)


def _mensagem(exc: DjangoValidationError) -> str:
    return exc.messages[0] if getattr(exc, "messages", None) else str(exc)


class PodeGerirFinanceiro(BasePermission):
    """Credenciais do gateway: só quem tem acesso total ao financeiro (leitura também expõe segredos)."""

    message = "Seu perfil não pode alterar a configuração de pagamento."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and pode_acessar(user, "financeiro", "PUT"))


def _membro_do_request(request):
    membro = resolver_membro_do_user(request.user, auto_link=True)
    if not membro:
        raise PermissionDenied("Nenhum associado vinculado a este usuário.")
    return membro


class ConfiguracaoPagamentoView(APIView):
    permission_classes = [IsAuthenticated, PodeGerirFinanceiro]

    def get(self, request):
        return Response(ConfiguracaoPagamentoSerializer(ConfiguracaoPagamento.atual()).data)

    def put(self, request):
        config = ConfiguracaoPagamento.atual()
        serializer = ConfiguracaoPagamentoSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data)

    patch = put


class TestarConfiguracaoView(APIView):
    """Confere se a chave salva conversa com o gateway."""

    permission_classes = [IsAuthenticated, PodeGerirFinanceiro]

    def post(self, request):
        config = ConfiguracaoPagamento.atual()
        if not config.api_key:
            raise ValidationError({"detail": "Salve a chave de API antes de testar."})
        try:
            resultado = gateway_da_config(config).testar()
        except GatewayError as exc:
            raise ValidationError({"detail": str(exc)})
        return Response(resultado)


class DisponibilidadeView(APIView):
    """Se o portal deve oferecer pagamento online e em quais formas."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(disponibilidade())


class CobrarAnuidadeView(APIView):
    """Associado gera a cobrança da própria anuidade."""

    permission_classes = [IsAuthenticated]

    def post(self, request, anuidade_id):
        membro = _membro_do_request(request)
        anuidade = get_object_or_404(
            Anuidade.objects.select_related("filiacao__membro"),
            pk=anuidade_id,
            filiacao__membro=membro,
        )
        serializer = CobrarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cobranca = cobrar_anuidade(anuidade, serializer.validated_data["metodo"])
        except DjangoValidationError as exc:
            raise ValidationError({"detail": _mensagem(exc)})
        return Response(CobrancaSerializer(cobranca).data, status=status.HTTP_201_CREATED)


class CobrarPedidoView(APIView):
    """Associado gera a cobrança de um pedido próprio da loja que aguarda pagamento."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pedido_id):
        membro = _membro_do_request(request)
        pedido = get_object_or_404(Order, pk=pedido_id, membro=membro)
        serializer = CobrarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cobranca = cobrar_pedido(pedido, serializer.validated_data["metodo"])
        except DjangoValidationError as exc:
            raise ValidationError({"detail": _mensagem(exc)})
        return Response(CobrancaSerializer(cobranca).data, status=status.HTTP_201_CREATED)


class MinhaCobrancaView(APIView):
    """Status de uma cobrança do associado (o portal consulta enquanto aguarda o Pix)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, cobranca_id):
        membro = _membro_do_request(request)
        cobranca = get_object_or_404(Cobranca, pk=cobranca_id, membro=membro)
        cobranca = sincronizar_cobranca(cobranca)
        return Response(CobrancaSerializer(cobranca).data)


class SimularPagamentoView(APIView):
    """Confirma uma cobrança do provedor simulado (dev/demo)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, cobranca_id):
        membro = _membro_do_request(request)
        cobranca = get_object_or_404(Cobranca, pk=cobranca_id, membro=membro)
        if cobranca.provedor != Cobranca.SIMULADO:
            raise PermissionDenied("Só cobranças simuladas podem ser confirmadas por aqui.")
        if cobranca.status != Cobranca.PENDENTE:
            raise ValidationError({"detail": "Cobrança não está aguardando pagamento."})
        cobranca = confirmar_cobranca(cobranca)
        return Response(CobrancaSerializer(cobranca).data)


class WebhookAsaasView(APIView):
    """
    POST /api/pagamentos/webhook/asaas/?schema=<schema>
    Autenticado pelo header `asaas-access-token` (token gerado na configuração da associação).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            raise NotFound("Associação não encontrada.")
        token = request.headers.get("asaas-access-token", "")
        payload = request.data if isinstance(request.data, dict) else {}
        with schema_context(tenant.schema_name):
            config = ConfiguracaoPagamento.atual()
            if not token or not hmac.compare_digest(token, config.webhook_token):
                raise PermissionDenied("Token inválido.")
            resultado = processar_webhook_asaas(payload)
        logger.info("Webhook Asaas [%s] %s → %s", tenant.schema_name, payload.get("event"), resultado)
        return Response({"resultado": resultado})


class _WebhookComTokenNaUrl(APIView):
    """
    POST /api/pagamentos/webhook/<provedor>/?schema=<schema>&token=<token>
    A URL vai em cada cobrança; o status sempre é relido na API do gateway.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    nome = ""

    def processar(self, request, payload: dict) -> str:
        raise NotImplementedError

    def post(self, request):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            raise NotFound("Associação não encontrada.")
        token = request.query_params.get("token", "")
        payload = request.data if isinstance(request.data, dict) else {}
        with schema_context(tenant.schema_name):
            config = ConfiguracaoPagamento.atual()
            if not token or not hmac.compare_digest(token, config.webhook_token):
                raise PermissionDenied("Token inválido.")
            resultado = self.processar(request, payload)
        logger.info("Webhook %s [%s] → %s", self.nome, tenant.schema_name, resultado)
        return Response({"resultado": resultado})


class WebhookPagBankView(_WebhookComTokenNaUrl):
    nome = "PagBank"

    def processar(self, request, payload):
        return processar_webhook_pagbank(payload)


class WebhookMercadoPagoView(_WebhookComTokenNaUrl):
    nome = "Mercado Pago"

    def processar(self, request, payload):
        return processar_webhook_mercadopago(payload, request.query_params)

