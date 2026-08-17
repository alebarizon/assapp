from django.urls import path

from .views import PublicTenantResolveView

app_name = "tenants"

urlpatterns = [
    path("public/resolve/", PublicTenantResolveView.as_view(), name="public-resolve"),
]
