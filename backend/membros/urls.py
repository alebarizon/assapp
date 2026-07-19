from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnuidadeViewSet,
    FiliacaoViewSet,
    MembroViewSet,
    MeuMembroView,
    MinhasAnuidadesView,
)

router = DefaultRouter()
router.register(r"membros", MembroViewSet, basename="membro")
router.register(r"filiacoes", FiliacaoViewSet, basename="filiacao")
router.register(r"anuidades", AnuidadeViewSet, basename="anuidade")

app_name = "membros"

urlpatterns = [
    # Self-service associado — antes do router (evita colisão com UUID)
    path("meu/", MeuMembroView.as_view(), name="meu"),
    path("meu/anuidades/", MinhasAnuidadesView.as_view(), name="meu-anuidades"),
    path("", include(router.urls)),
]
