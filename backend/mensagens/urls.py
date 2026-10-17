from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import ConversaViewSet, MinhasConversasViewSet

app_name = "mensagens"

router = SimpleRouter()
router.register(r"my", MinhasConversasViewSet, basename="minhas-conversas")
router.register(r"", ConversaViewSet, basename="conversa")

urlpatterns = [path("", include(router.urls))]
