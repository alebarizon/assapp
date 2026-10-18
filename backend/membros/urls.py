from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnuidadeViewSet,
    FiliacaoViewSet,
    MembroViewSet,
    MeuMembroView,
    MinhaCarteirinhaPdfView,
    MinhaCarteirinhaView,
    MinhasAnuidadesView,
    VerificarCarteirinhaView,
    DiretorioPublicoView,
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
    path("meu/carteirinha/", MinhaCarteirinhaView.as_view(), name="minha-carteirinha"),
    path("meu/carteirinha/pdf/", MinhaCarteirinhaPdfView.as_view(), name="minha-carteirinha-pdf"),
    path("public/carteirinha/<str:codigo>/", VerificarCarteirinhaView.as_view(), name="verificar-carteirinha"),
    path("public/diretorio/", DiretorioPublicoView.as_view(), name="diretorio-publico"),
    path("", include(router.urls)),
]
