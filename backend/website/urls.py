from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PublicDiretoriaView,
    PublicSitePageView,
    PublicSiteView,
    SitePageViewSet,
    WebsiteConfigView,
)

app_name = "website"

router = DefaultRouter()
router.register(r"pages", SitePageViewSet, basename="site-page")

urlpatterns = [
    path("config/", WebsiteConfigView.as_view(), name="config"),
    path("public/", PublicSiteView.as_view(), name="public"),
    path("public/pages/<slug:slug>/", PublicSitePageView.as_view(), name="public-page"),
    path("public/diretoria/", PublicDiretoriaView.as_view(), name="public-diretoria"),
    path("", include(router.urls)),
]
