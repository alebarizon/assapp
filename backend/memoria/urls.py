from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ContextoHistoricoViewSet, TimelineInstitucionalViewSet

router = DefaultRouter()
router.register(r"contextos", ContextoHistoricoViewSet, basename="contexto")
router.register(r"timeline", TimelineInstitucionalViewSet, basename="timeline")

app_name = "memoria"

urlpatterns = [
    path("", include(router.urls)),
]
