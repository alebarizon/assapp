from django.urls import path
from rest_framework.routers import SimpleRouter

from .equipe_views import DefinirSenhaView, EquipeViewSet, EsqueciSenhaView
from .views import (
    AssociationSetupView,
    CurrentUserView,
    PublicPlansView,
    RegisterAssociationView,
    SimpleLoginView,
    TenantStatusView,
)

app_name = "accounts"

router = SimpleRouter()
router.register(r"equipe", EquipeViewSet, basename="equipe")

urlpatterns = [
    path("simple/login/", SimpleLoginView.as_view(), name="simple-login"),
    path("register/", RegisterAssociationView.as_view(), name="register"),
    path("plans/", PublicPlansView.as_view(), name="plans"),
    path("setup/", AssociationSetupView.as_view(), name="setup"),
    path("tenant-status/", TenantStatusView.as_view(), name="tenant-status"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("senha/esqueci/", EsqueciSenhaView.as_view(), name="senha-esqueci"),
    path("senha/definir/", DefinirSenhaView.as_view(), name="senha-definir"),
    *router.urls,
]
