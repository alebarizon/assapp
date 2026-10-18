"""
API de publicações.

Painel:  /api/publicacoes/                       CRUD (módulo publicacoes)
Portal:  /api/publicacoes/minhas/                vitrine com situação de acesso
         /api/publicacoes/minhas/<id>/arquivo/   download conforme o paywall
Público: /api/publicacoes/public/?schema=        catálogo do site
         /api/publicacoes/public/<slug>/?schema=
         /api/publicacoes/public/<slug>/arquivo/?schema=   só acesso aberto
"""
from django.db.models import F
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_tenants.utils import schema_context
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mandatos.permissions import IsBoardOrAdmin
from membros.services import membro_adimplente, resolver_membro_do_user
from tenants.resolvers import resolve_tenant_from_request

from .models import AcessoPublicacao, Publicacao
from .serializers import PublicacaoPublicaSerializer, PublicacaoSerializer
from .services import acesso


def _publicadas():
    return Publicacao.objects.filter(publicada=True).select_related("catalog_item")


def _baixar(pub: Publicacao):
    if not pub.arquivo:
        raise NotFound("Esta publicação ainda não tem arquivo.")
    Publicacao.objects.filter(pk=pub.pk).update(downloads=F("downloads") + 1)
    nome = f"{pub.slug}.{pub.arquivo.name.rsplit('.', 1)[-1]}" if "." in pub.arquivo.name else pub.slug
    return FileResponse(pub.arquivo.open("rb"), as_attachment=True, filename=nome)


class PublicacaoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "publicacoes"
    serializer_class = PublicacaoSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = None
    lookup_value_regex = r"[0-9a-fA-F-]{36}"

    def get_queryset(self):
        qs = Publicacao.objects.select_related("catalog_item")
        tipo = self.request.query_params.get("tipo")
        if tipo:
            qs = qs.filter(tipo=tipo)
        return qs.order_by("-created_at")

    def perform_destroy(self, instance):
        item = instance.catalog_item
        instance.delete()
        if item and item.is_active:
            item.is_active = False
            item.save(update_fields=["is_active", "updated_at"])

    @action(detail=True, methods=["get"])
    def arquivo(self, request, pk=None):
        pub = self.get_object()
        if not pub.arquivo:
            raise NotFound("Sem arquivo.")
        return FileResponse(pub.arquivo.open("rb"), as_attachment=True, filename=pub.arquivo.name.rsplit("/", 1)[-1])


class MinhasPublicacoesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membro = resolver_membro_do_user(request.user, auto_link=True)
        adimplente = membro_adimplente(membro)
        dados = []
        for pub in _publicadas():
            item = PublicacaoPublicaSerializer(pub, context={"request": request}).data
            situacao = acesso(pub, request.user, membro)
            loja = pub.catalog_item if pub.catalog_item and pub.catalog_item.is_active else None
            item.update(situacao)
            item["catalog_item"] = str(loja.id) if loja and not situacao["liberado"] else None
            item["preco_final"] = f"{loja.preco_para(adimplente):.2f}" if loja else None
            dados.append(item)
        return Response(dados)


class MinhaPublicacaoArquivoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        pub = get_object_or_404(_publicadas(), pk=pk)
        membro = resolver_membro_do_user(request.user, auto_link=True)
        situacao = acesso(pub, request.user, membro)
        if not situacao["liberado"]:
            raise PermissionDenied(situacao["motivo_display"])
        return _baixar(pub)


class _PublicoMixin:
    permission_classes = [AllowAny]
    authentication_classes = []

    def _schema(self, request):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            raise NotFound("Associação não encontrada. Informe ?schema=.")
        return tenant.schema_name


class PublicPublicacaoListView(_PublicoMixin, APIView):
    def get(self, request):
        with schema_context(self._schema(request)):
            qs = _publicadas()
            tipo = request.query_params.get("tipo")
            if tipo:
                qs = qs.filter(tipo=tipo)
            return Response(PublicacaoPublicaSerializer(qs, many=True, context={"request": request}).data)


class PublicPublicacaoDetailView(_PublicoMixin, APIView):
    def get(self, request, slug):
        with schema_context(self._schema(request)):
            pub = get_object_or_404(_publicadas(), slug=slug)
            return Response(PublicacaoPublicaSerializer(pub, context={"request": request}).data)


class PublicPublicacaoArquivoView(_PublicoMixin, APIView):
    def get(self, request, slug):
        with schema_context(self._schema(request)):
            pub = get_object_or_404(_publicadas(), slug=slug)
            if pub.acesso != AcessoPublicacao.PUBLICO:
                raise PermissionDenied("Acesse pelo portal do associado.")
            return _baixar(pub)
