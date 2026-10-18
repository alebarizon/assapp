"""URL configuration — AssApp API."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .certificados_views import CertificadoPdfView, CertificadoVerificacaoView
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
    path("api/ecommerce/", include("ecommerce.urls")),
    path("api/website/", include("website.urls")),
    path("api/courses/", include("courses.urls")),
    path("api/formularios/", include("formularios.urls")),
    path("api/contatos/", include("contatos.urls")),
    path("api/suporte/", include("support.urls")),
    path("api/mensagens/", include("mensagens.urls")),
    path("api/pagamentos/", include("payments.urls")),
    path("api/certificados/<str:code>/", CertificadoVerificacaoView.as_view(), name="certificado-verificar"),
    path("api/certificados/<str:code>/pdf/", CertificadoPdfView.as_view(), name="certificado-pdf"),
    path("api/tenants/", include("tenants.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
