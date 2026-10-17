"""
API de Mensagens (diretoria ↔ associado).

Diretoria: /api/mensagens/                 conversas, iniciar (1, vários ou todos os ativos), responder, arquivar
Associado: /api/mensagens/my/              suas conversas, iniciar com a secretaria, responder
"""
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mandatos.permissions import IsBoardOrAdmin
from membros.models import Membro
from membros.services import resolver_membro_do_user

from .models import Conversa
from .serializers import (
    ConversaDetailSerializer,
    ConversaListSerializer,
    NovaConversaDiretoriaSerializer,
    NovaConversaSerializer,
    RespostaSerializer,
)
from .services import iniciar_pela_diretoria, iniciar_pelo_associado, responder

UUID_LOOKUP = r"[0-9a-fA-F-]{36}"


class ConversaViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "mensagens"
    lookup_value_regex = UUID_LOOKUP

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "diretoria": True}

    def get_queryset(self):
        return Conversa.objects.select_related("membro")

    def list(self, request):
        qs = self.get_queryset()
        params = request.query_params
        qs = qs.filter(status=params.get("status") or Conversa.ABERTA)
        if params.get("nao_lidas") == "true":
            qs = qs.filter(lida_pela_diretoria=False)
        if params.get("membro"):
            qs = qs.filter(membro_id=params["membro"])
        if params.get("search"):
            termo = params["search"]
            qs = qs.filter(
                Q(assunto__icontains=termo) | Q(membro__nome_completo__icontains=termo) | Q(membro__email__icontains=termo)
            )
        return Response(ConversaListSerializer(qs[:300], many=True, context=self.get_serializer_context()).data)

    def create(self, request):
        serializer = NovaConversaDiretoriaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data
        membros = (
            Membro.objects.filter(ativo=True) if dados["todos_ativos"] else Membro.objects.filter(id__in=dados["membros"])
        )
        if not membros.exists():
            raise ValidationError({"membros": "Nenhum associado encontrado."})
        conversas = iniciar_pela_diretoria(request.user, membros, dados["assunto"], dados["texto"], dados["notificar"])
        corpo = {"criadas": len(conversas)}
        if len(conversas) == 1:
            corpo["id"] = str(conversas[0].id)
        return Response(corpo, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        conversa = self.get_object()
        if not conversa.lida_pela_diretoria:
            conversa.lida_pela_diretoria = True
            conversa.save(update_fields=["lida_pela_diretoria"])
        return Response(ConversaDetailSerializer(conversa, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"], url_path="responder")
    def responder_conversa(self, request, pk=None):
        conversa = self.get_object()
        serializer = RespostaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        responder(conversa, request.user, serializer.validated_data["texto"], da_diretoria=True)
        conversa.refresh_from_db()
        return Response(ConversaDetailSerializer(conversa, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def arquivar(self, request, pk=None):
        conversa = self.get_object()
        conversa.status = Conversa.ARQUIVADA if request.data.get("arquivar", True) else Conversa.ABERTA
        conversa.save(update_fields=["status"])
        return Response({"status": conversa.status})

    @action(detail=False, methods=["get"])
    def resumo(self, request):
        qs = self.get_queryset().filter(status=Conversa.ABERTA)
        return Response({"abertas": qs.count(), "nao_lidas": qs.filter(lida_pela_diretoria=False).count()})


class MinhasConversasViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    lookup_value_regex = UUID_LOOKUP

    def get_membro(self):
        membro = resolver_membro_do_user(self.request.user, auto_link=True)
        if not membro:
            raise NotFound("Perfil de associado não encontrado.")
        return membro

    def _conversa(self, pk):
        conversa = Conversa.objects.select_related("membro").filter(pk=pk, membro=self.get_membro()).first()
        if not conversa:
            raise NotFound("Conversa não encontrada.")
        return conversa

    def list(self, request):
        qs = Conversa.objects.filter(membro=self.get_membro()).select_related("membro")
        return Response(ConversaListSerializer(qs, many=True).data)

    def create(self, request):
        serializer = NovaConversaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversa = iniciar_pelo_associado(
            request.user, self.get_membro(), serializer.validated_data["assunto"], serializer.validated_data["texto"]
        )
        return Response(ConversaDetailSerializer(conversa).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        conversa = self._conversa(pk)
        if not conversa.lida_pelo_associado:
            conversa.lida_pelo_associado = True
            conversa.save(update_fields=["lida_pelo_associado"])
        return Response(ConversaDetailSerializer(conversa).data)

    @action(detail=True, methods=["post"], url_path="responder")
    def responder_conversa(self, request, pk=None):
        conversa = self._conversa(pk)
        serializer = RespostaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        responder(conversa, request.user, serializer.validated_data["texto"], da_diretoria=False)
        conversa.refresh_from_db()
        return Response(ConversaDetailSerializer(conversa).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def resumo(self, request):
        qs = Conversa.objects.filter(membro=self.get_membro())
        return Response({"nao_lidas": qs.filter(lida_pelo_associado=False).count()})
