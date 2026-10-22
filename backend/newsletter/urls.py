from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CampanhaViewSet, DescadastrarPublicView, DescadastroViewSet, ReguaViewSet

app_name = "newsletter"

router = DefaultRouter()
router.register(r"campanhas", CampanhaViewSet, basename="campanha")
router.register(r"reguas", ReguaViewSet, basename="regua")
router.register(r"descadastros", DescadastroViewSet, basename="descadastro")

urlpatterns = [
    path("public/descadastrar/", DescadastrarPublicView.as_view(), name="descadastrar"),
] + router.urls
