from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CatalogoView, WebhookSaidaViewSet

app_name = "integracoes"

router = DefaultRouter()
router.register("webhooks", WebhookSaidaViewSet, basename="webhook")

urlpatterns = [
    path("catalogo/", CatalogoView.as_view(), name="catalogo"),
    path("", include(router.urls)),
]
