from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EventoAcademicoViewSet,
    InscricaoEventoViewSet,
    ParecerViewSet,
    SubmissaoTrabalhoViewSet,
)

router = DefaultRouter()
router.register(r"eventos", EventoAcademicoViewSet, basename="evento")
router.register(r"submissoes", SubmissaoTrabalhoViewSet, basename="submissao")
router.register(r"pareceres", ParecerViewSet, basename="parecer")
router.register(r"inscricoes", InscricaoEventoViewSet, basename="inscricao")

app_name = "eventos"

urlpatterns = [
    path("", include(router.urls)),
]
