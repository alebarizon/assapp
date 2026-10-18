from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AtividadeProgramacaoViewSet,
    MeuParecerViewSet,
    PublicAnaisView,
    PublicTrabalhoPdfView,
    PublicTrabalhoView,
    TrabalhoPublicadoViewSet,
    MinhasChamadasView,
    MinhaSubmissaoViewSet,
    EventoAcademicoViewSet,
    InscricaoEventoViewSet,
    ParecerViewSet,
    PublicEventoDetailView,
    PublicEventoListView,
    SubmissaoTrabalhoViewSet,
)

router = DefaultRouter()
router.register(r"eventos", EventoAcademicoViewSet, basename="evento")
router.register(r"submissoes", SubmissaoTrabalhoViewSet, basename="submissao")
router.register(r"pareceres", ParecerViewSet, basename="parecer")
router.register(r"inscricoes", InscricaoEventoViewSet, basename="inscricao")
router.register(r"programacao", AtividadeProgramacaoViewSet, basename="programacao")
router.register(r"trabalhos-publicados", TrabalhoPublicadoViewSet, basename="trabalho-publicado")
router.register(r"my/submissoes", MinhaSubmissaoViewSet, basename="minha-submissao")
router.register(r"my/pareceres", MeuParecerViewSet, basename="meu-parecer")

app_name = "eventos"

urlpatterns = [
    path("my/chamadas/", MinhasChamadasView.as_view(), name="minhas-chamadas"),
    path("public/", PublicEventoListView.as_view(), name="public-eventos"),
    path("public/<slug:slug>/anais/", PublicAnaisView.as_view(), name="public-anais"),
    path("public/<slug:slug>/anais/<slug:trabalho_slug>/", PublicTrabalhoView.as_view(), name="public-trabalho"),
    path(
        "public/<slug:slug>/anais/<slug:trabalho_slug>/pdf/",
        PublicTrabalhoPdfView.as_view(),
        name="public-trabalho-pdf",
    ),
    path("public/<slug:slug>/", PublicEventoDetailView.as_view(), name="public-evento-detail"),
    path("", include(router.urls)),
]
