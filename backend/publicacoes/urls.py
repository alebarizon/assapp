from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    MinhaPublicacaoArquivoView,
    MinhasPublicacoesView,
    PublicacaoViewSet,
    PublicPublicacaoArquivoView,
    PublicPublicacaoDetailView,
    PublicPublicacaoListView,
)

app_name = "publicacoes"

router = DefaultRouter()
router.register(r"", PublicacaoViewSet, basename="publicacao")

urlpatterns = [
    path("minhas/", MinhasPublicacoesView.as_view(), name="minhas"),
    path("minhas/<uuid:pk>/arquivo/", MinhaPublicacaoArquivoView.as_view(), name="minhas-arquivo"),
    path("public/", PublicPublicacaoListView.as_view(), name="public-list"),
    path("public/<slug:slug>/", PublicPublicacaoDetailView.as_view(), name="public-detail"),
    path("public/<slug:slug>/arquivo/", PublicPublicacaoArquivoView.as_view(), name="public-arquivo"),
] + router.urls
