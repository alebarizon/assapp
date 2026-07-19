from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, MeuDocumentoDownloadView, MeusDocumentosView

app_name = "documents"

router = DefaultRouter()
# Prefixo vazio sob /api/documents/ → list/create em /api/documents/
router.register(r"", DocumentViewSet, basename="document")

urlpatterns = [
    path("meus/", MeusDocumentosView.as_view(), name="meus"),
    path(
        "meus/<uuid:pk>/download/",
        MeuDocumentoDownloadView.as_view(),
        name="meus-download",
    ),
] + router.urls
