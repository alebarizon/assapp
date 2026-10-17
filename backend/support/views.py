"""
API do Suporte.

Diretoria da associação: chamados da própria associação (abrir, responder, fechar/reabrir).
Equipe Gesttora (superadmin): todos os chamados, status, prioridade e notas internas.

GET/POST /api/suporte/                  lista · abrir (multipart: assunto, categoria, mensagem, anexos[])
GET      /api/suporte/{id}/             detalhe + mensagens (marca como lido)
POST     /api/suporte/{id}/responder/   texto, interna?, anexos[]
POST     /api/suporte/{id}/status/      {status, prioridade?}
GET      /api/suporte/resumo/           contagem por status + não lidos
"""
from django.db.models import Count, Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mandatos.permissions import IsBoardOrAdmin

from .models import Chamado
from .serializers import AbrirChamadoSerializer, ChamadoDetailSerializer, ChamadoListSerializer, ResponderSerializer
from .services import abrir_chamado, is_equipe, registrar_mudanca_status, tenant_do_user, validar_anexos
from .services import responder as responder_chamado


class ChamadoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "suporte"
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    pagination_class = None

    @property
    def equipe(self) -> bool:
        return is_equipe(self.request.user)

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "equipe": self.equipe}

    def get_serializer_class(self):
        return ChamadoListSerializer if self.action == "list" else ChamadoDetailSerializer

    def get_queryset(self):
        qs = Chamado.objects.select_related("tenant")
        if not self.equipe:
            tenant = tenant_do_user(self.request.user)
            qs = qs.filter(tenant=tenant) if tenant else qs.none()
        if self.action == "list":
            params = self.request.query_params
            if params.get("status") == "abertos":
                qs = qs.exclude(status__in=Chamado.STATUS_ENCERRADOS)
            elif params.get("status"):
                qs = qs.filter(status=params["status"])
            if params.get("categoria"):
                qs = qs.filter(categoria=params["categoria"])
            if self.equipe and params.get("tenant"):
                qs = qs.filter(tenant_id=params["tenant"])
            if params.get("search"):
                termo = params["search"]
                qs = qs.filter(Q(assunto__icontains=termo) | Q(tenant__name__icontains=termo) | Q(autor_email__icontains=termo))
        return qs

    def create(self, request):
        if self.equipe:
            raise PermissionDenied("Chamados são abertos pelas associações.")
        serializer = AbrirChamadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        anexos = validar_anexos(request.FILES.getlist("anexos"))
        chamado = abrir_chamado(request.user, serializer.validated_data, anexos)
        return Response(ChamadoDetailSerializer(chamado, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        chamado = self.get_object()
        campo = "lido_pela_equipe" if self.equipe else "lido_pela_associacao"
        if not getattr(chamado, campo):
            setattr(chamado, campo, True)
            chamado.save(update_fields=[campo])
        return Response(self.get_serializer(chamado).data)

    @action(detail=True, methods=["post"])
    def responder(self, request, pk=None):
        chamado = self.get_object()
        serializer = ResponderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        anexos = validar_anexos(request.FILES.getlist("anexos"))
        responder_chamado(chamado, request.user, serializer.validated_data["texto"], anexos, serializer.validated_data["interna"])
        chamado.refresh_from_db()
        return Response(self.get_serializer(chamado).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="status")
    def alterar_status(self, request, pk=None):
        chamado = self.get_object()
        novo = request.data.get("status")
        prioridade = request.data.get("prioridade")
        validos = dict(Chamado.STATUS_CHOICES)
        if novo and novo not in validos:
            raise ValidationError({"status": "Status inválido."})
        if not self.equipe:
            if prioridade:
                raise PermissionDenied("Somente a equipe Gesttora altera a prioridade.")
            if novo not in (Chamado.FECHADO, Chamado.ABERTO):
                raise PermissionDenied("A associação pode apenas fechar ou reabrir o chamado.")
        if prioridade:
            if prioridade not in dict(Chamado.PRIORIDADE_CHOICES):
                raise ValidationError({"prioridade": "Prioridade inválida."})
            chamado.prioridade = prioridade
            chamado.save(update_fields=["prioridade", "updated_at"])
        if novo:
            registrar_mudanca_status(chamado, request.user, novo)
        return Response(self.get_serializer(chamado).data)

    @action(detail=False, methods=["get"])
    def resumo(self, request):
        qs = self.get_queryset()
        campo_lido = "lido_pela_equipe" if self.equipe else "lido_pela_associacao"
        por_status = {s: 0 for s, _ in Chamado.STATUS_CHOICES}
        for row in qs.values("status").annotate(total=Count("id")):
            por_status[row["status"]] = row["total"]
        return Response({"por_status": por_status, "nao_lidos": qs.filter(**{campo_lido: False}).count()})
