"""
API REST — Memória Institucional (H1)

Preservação ativa: cada registro vincula quem decidiu, o quê, por quê e em qual mandato.
"""
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mandatos.models import Mandato
from mandatos.permissions import IsBoardOrAdmin

from .models import ContextoHistorico, TimelineInstitucional
from .serializers import (
    ContextoHistoricoCreateSerializer,
    ContextoHistoricoSerializer,
    TimelineInstitucionalSerializer,
)


class ContextoHistoricoViewSet(viewsets.ModelViewSet):
    """
    H1 — CRUD de contextos históricos com vínculo a mandatos.
    """
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]

    def get_queryset(self):
        qs = ContextoHistorico.objects.select_related("mandato", "autor")
        if self.request.query_params.get("incluir_arquivados") != "true":
            qs = qs.filter(arquivado=False)

        mandato_id = self.request.query_params.get("mandato")
        if mandato_id:
            qs = qs.filter(mandato_id=mandato_id)

        tipo = self.request.query_params.get("tipo")
        if tipo:
            qs = qs.filter(tipo=tipo)

        busca = self.request.query_params.get("q")
        if busca:
            qs = qs.filter(
                Q(titulo__icontains=busca)
                | Q(conteudo__icontains=busca)
                | Q(decisao__icontains=busca)
                | Q(motivo__icontains=busca)
            )

        tags = self.request.query_params.get("tags")
        if tags:
            for tag in tags.split(","):
                qs = qs.filter(tags__contains=[tag.strip()])

        return qs.order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ContextoHistoricoCreateSerializer
        return ContextoHistoricoSerializer

    def perform_create(self, serializer):
        # H1: registra autor automaticamente
        serializer.save(autor=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contexto = serializer.save(autor=request.user)
        return Response(
            ContextoHistoricoSerializer(contexto).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def arquivar(self, request, pk=None):
        """Arquiva registro preservando metadados (não deleta)."""
        contexto = self.get_object()
        contexto.arquivado = True
        contexto.save(update_fields=["arquivado", "updated_at"])
        return Response(ContextoHistoricoSerializer(contexto).data)

    @action(detail=False, methods=["get"])
    def decisoes_recentes(self, request):
        """Decisões recentes — usado no onboarding e dashboard."""
        limite = int(request.query_params.get("limite", 10))
        qs = self.get_queryset().filter(tipo="decisao")[:limite]
        return Response(ContextoHistoricoSerializer(qs, many=True).data)


class TimelineInstitucionalViewSet(viewsets.ReadOnlyModelViewSet):
    """Timeline cronológica por mandato (H1)."""
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    serializer_class = TimelineInstitucionalSerializer

    def get_queryset(self):
        qs = TimelineInstitucional.objects.select_related("mandato")
        mandato_id = self.request.query_params.get("mandato")
        if mandato_id:
            qs = qs.filter(mandato_id=mandato_id)
        return qs.order_by("-data_evento")

    @action(detail=False, methods=["get"])
    def por_mandato_ativo(self, request):
        """Timeline do mandato ativo."""
        mandato = Mandato.get_ativo()
        if not mandato:
            return Response({"detail": "Nenhum mandato ativo."}, status=404)
        qs = self.get_queryset().filter(mandato=mandato)
        return Response(TimelineInstitucionalSerializer(qs, many=True).data)
