from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import ContatoPublicoView, ContatoViewSet, EtiquetaViewSet

app_name = "contatos"

router = SimpleRouter()
router.register(r"etiquetas", EtiquetaViewSet, basename="etiqueta")
router.register(r"", ContatoViewSet, basename="contato")

urlpatterns = [
    path("public/", ContatoPublicoView.as_view(), name="public-contato"),
    path("", include(router.urls)),
]
