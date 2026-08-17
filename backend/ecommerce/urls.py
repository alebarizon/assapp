from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CartViewSet, CatalogItemViewSet, EcommerceResumoView, OrderViewSet, PublicCatalogView

app_name = "ecommerce"

router = DefaultRouter()
router.register(r"catalog", CatalogItemViewSet, basename="catalog")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("public/catalog/", PublicCatalogView.as_view(), name="public-catalog"),
    path("resumo/", EcommerceResumoView.as_view(), name="resumo"),
    path("cart/", CartViewSet.as_view({"get": "list"}), name="cart"),
    path("cart/add/", CartViewSet.as_view({"post": "add_item"}), name="cart-add"),
    path(
        "cart/update/<uuid:item_id>/",
        CartViewSet.as_view({"patch": "update_item"}),
        name="cart-update",
    ),
    path(
        "cart/remove/<uuid:item_id>/",
        CartViewSet.as_view({"delete": "remove_item"}),
        name="cart-remove",
    ),
    path("cart/clear/", CartViewSet.as_view({"post": "clear_cart"}), name="cart-clear"),
    path("cart/checkout/", CartViewSet.as_view({"post": "checkout"}), name="cart-checkout"),
    path("", include(router.urls)),
]
