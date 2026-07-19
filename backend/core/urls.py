"""URL configuration — AssApp API."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .views import health_check, api_root

urlpatterns = [
    path("", api_root, name="api-root"),
    path("health/", health_check, name="health"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/mandatos/", include("mandatos.urls")),
    path("api/memoria/", include("memoria.urls")),
    path("api/eventos/", include("eventos.urls")),
    path("api/membros/", include("membros.urls")),
    path("api/finance/", include("finance.urls")),
    path("api/documents/", include("documents.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
