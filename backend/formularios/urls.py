from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import FormularioViewSet, MeusFormulariosViewSet, PublicConviteView, PublicFormularioView

app_name = "formularios"

router = SimpleRouter()
router.register(r"my", MeusFormulariosViewSet, basename="meus-formularios")
router.register(r"", FormularioViewSet, basename="formulario")

urlpatterns = [
    path("public/f/<uuid:token>/", PublicFormularioView.as_view(), name="public-formulario"),
    path("public/r/<uuid:token>/", PublicConviteView.as_view(), name="public-convite"),
    path("", include(router.urls)),
]
