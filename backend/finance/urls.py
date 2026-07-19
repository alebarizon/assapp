from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoriesView,
    FinancialDashboardView,
    MonthlyReportView,
    SendReportEmailView,
    TransactionViewSet,
)

app_name = "finance"

router = DefaultRouter()
router.register(r"transactions", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("dashboard/", FinancialDashboardView.as_view(), name="dashboard"),
    path("monthly-report/", MonthlyReportView.as_view(), name="monthly-report"),
    path("send-report-email/", SendReportEmailView.as_view(), name="send-report-email"),
    path("categories/", CategoriesView.as_view(), name="categories"),
    path("", include(router.urls)),
]
