"""
API das integrações (/api/integracoes/), módulo `integracoes` (gestor).

    GET  catalogo/                          conectores com a situação nesta associação
    CRUD webhooks/                          webhooks de saída
    POST webhooks/{id}/testar/              entrega um evento "ping" na hora
    POST webhooks/{id}/regenerar-segredo/
    GET  webhooks/{id}/entregas/            últimas 50 entregas
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.access import pode_acessar
from mandatos.permissions import IsBoardOrAdmin

from . import services
from .conectores import CATEGORIAS, catalogo
from .models import EVENTOS, WebhookSaida
from .serializers import EntregaWebhookSerializer, WebhookSaidaSerializer


class CatalogoView(APIView):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "integracoes"

    def get(self, request):
        return Response(
            {
                "categorias": [{"slug": s, "label": l} for s, l in CATEGORIAS],
                "conectores": catalogo(),
                "eventos": [{"slug": s, "label": l} for s, l in EVENTOS],
                "pode_configurar_pagamento": pode_acessar(request.user, "financeiro", "PUT"),
            }
        )


class WebhookSaidaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "integracoes"
    serializer_class = WebhookSaidaSerializer
    pagination_class = None
    queryset = WebhookSaida.objects.all()
    lookup_value_regex = r"[0-9a-fA-F-]{36}"

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        reativado = serializer.validated_data.get("ativo") and not serializer.instance.ativo
        webhook = serializer.save()
        if reativado:
            webhook.falhas_seguidas = 0
            webhook.save(update_fields=["falhas_seguidas"])

    @action(detail=True, methods=["post"])
    def testar(self, request, pk=None):
        entrega = services.testar(self.get_object())
        return Response(EntregaWebhookSerializer(entrega).data)

    @action(detail=True, methods=["post"], url_path="regenerar-segredo")
    def regenerar_segredo(self, request, pk=None):
        webhook = self.get_object()
        webhook.regenerar_segredo()
        return Response(self.get_serializer(webhook).data)

    @action(detail=True, methods=["get"])
    def entregas(self, request, pk=None):
        entregas = self.get_object().entregas.all()[:50]
        return Response(EntregaWebhookSerializer(entregas, many=True).data)
