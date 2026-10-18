from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AssembleiaViewSet,
    MinhaAtaPdfView,
    MinhaGovernancaView,
    MinhaPresencaView,
    VotacaoViewSet,
    VotarView,
)

app_name = "governanca"

router = DefaultRouter()
router.register(r"assembleias", AssembleiaViewSet, basename="assembleia")
router.register(r"votacoes", VotacaoViewSet, basename="votacao")

urlpatterns = [
    path("minhas/", MinhaGovernancaView.as_view(), name="minhas"),
    path("minhas/votacoes/<uuid:pk>/votar/", VotarView.as_view(), name="votar"),
    path("minhas/assembleias/<uuid:pk>/presenca/", MinhaPresencaView.as_view(), name="minha-presenca"),
    path("minhas/assembleias/<uuid:pk>/ata-pdf/", MinhaAtaPdfView.as_view(), name="minha-ata-pdf"),
] + router.urls
