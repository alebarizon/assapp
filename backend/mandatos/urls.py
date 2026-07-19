from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MandatoViewSet, OnboardingEtapaViewSet, TransicaoMandatoViewSet

router = DefaultRouter()
router.register(r"mandatos", MandatoViewSet, basename="mandato")
router.register(r"transicoes", TransicaoMandatoViewSet, basename="transicao")
router.register(r"onboarding", OnboardingEtapaViewSet, basename="onboarding")

app_name = "mandatos"

urlpatterns = [
    path("", include(router.urls)),
]
