"""API — website público e CMS tenant."""
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mandatos.models import Mandato
from mandatos.permissions import IsBoardOrAdmin
from mandatos.serializers import MandatoDetailSerializer

from .models import PageType, SitePage, WebsiteConfig
from .serializers import SitePageSerializer, WebsiteConfigSerializer
from .services import get_or_create_config
from tenants.resolvers import resolve_tenant_from_request
from ecommerce.models import CatalogItem, CatalogItemType
from ecommerce.serializers import PublicCatalogItemSerializer


def _diretoria_publica():
    mandato = Mandato.get_ativo()
    if not mandato:
        return None
    data = MandatoDetailSerializer(mandato).data
    return {
        "titulo": data.get("titulo"),
        "data_inicio": data.get("data_inicio"),
        "data_fim": data.get("data_fim"),
        "cargos": data.get("cargos", []),
    }


class WebsiteConfigView(APIView):
    """GET/PATCH config singleton — diretoria."""

    permission_classes = [IsAuthenticated, IsBoardOrAdmin]

    def get(self, request):
        config = get_or_create_config()
        return Response(WebsiteConfigSerializer(config).data)

    def patch(self, request):
        config = get_or_create_config()
        ser = WebsiteConfigSerializer(config, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class SitePageViewSet(viewsets.ModelViewSet):
    serializer_class = SitePageSerializer
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    lookup_field = "slug"

    def get_queryset(self):
        qs = SitePage.objects.all()
        page_type = self.request.query_params.get("page_type")
        if page_type:
            qs = qs.filter(page_type=page_type)
        return qs.order_by("order", "-published_at")

    def perform_create(self, serializer):
        page = serializer.save()
        if page.is_published and not page.published_at:
            page.published_at = timezone.now()
            page.save(update_fields=["published_at"])


class PublicSiteView(APIView):
    """Payload completo da home pública."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            return Response(
                {"detail": "Informe ?schema=nome_do_tenant"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with schema_context(tenant.schema_name):
            config = WebsiteConfig.objects.filter(is_published=True).first()
            if not config:
                return Response(
                    {"detail": "Site não publicado para este tenant."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            news = SitePage.objects.filter(
                is_published=True,
                page_type=PageType.NOTICIA,
            ).order_by("-published_at", "-created_at")[:6]
            associe_items = CatalogItem.objects.filter(
                is_active=True,
                item_type=CatalogItemType.ANUIDADE,
            ).order_by("price", "name")[:12]
            return Response(
                {
                    "schema": tenant.schema_name,
                    "tenant_name": tenant.name,
                    "config": WebsiteConfigSerializer(config).data,
                    "news": SitePageSerializer(news, many=True).data,
                    "diretoria": _diretoria_publica(),
                    "associe_se_items": PublicCatalogItemSerializer(
                        associe_items, many=True
                    ).data,
                }
            )


class PublicSitePageView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            return Response({"detail": "Informe ?schema="}, status=status.HTTP_400_BAD_REQUEST)
        with schema_context(tenant.schema_name):
            try:
                page = SitePage.objects.get(slug=slug, is_published=True)
            except SitePage.DoesNotExist:
                return Response({"detail": "Página não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            config = WebsiteConfig.objects.filter(is_published=True).first()
            return Response(
                {
                    "schema": tenant.schema_name,
                    "config": WebsiteConfigSerializer(config).data if config else None,
                    "page": SitePageSerializer(page).data,
                }
            )


class PublicDiretoriaView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            return Response({"detail": "Informe ?schema="}, status=status.HTTP_400_BAD_REQUEST)
        with schema_context(tenant.schema_name):
            data = _diretoria_publica()
            if not data:
                return Response({"detail": "Sem mandato ativo."}, status=status.HTTP_404_NOT_FOUND)
            return Response(data)
