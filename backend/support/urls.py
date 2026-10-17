from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import ChamadoViewSet

app_name = "support"

router = SimpleRouter()
router.register(r"", ChamadoViewSet, basename="chamado")

urlpatterns = [path("", include(router.urls))]
