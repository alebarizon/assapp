"""Serializers — e-commerce Gesttora."""
from rest_framework import serializers

from .models import Cart, CartItem, CatalogItem, Order, OrderItem


class CatalogItemSerializer(serializers.ModelSerializer):
    item_type_display = serializers.CharField(source="get_item_type_display", read_only=True)
    evento_titulo = serializers.CharField(source="evento.titulo", read_only=True, allow_null=True)

    class Meta:
        model = CatalogItem
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "item_type",
            "item_type_display",
            "price",
            "currency",
            "inventory_count",
            "image_url",
            "is_active",
            "anuidade_ano",
            "tipo_filiacao",
            "evento",
            "evento_titulo",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class PublicCatalogItemSerializer(serializers.ModelSerializer):
    """Vitrine pública — sem dados internos de estoque."""

    item_type_display = serializers.CharField(source="get_item_type_display", read_only=True)

    class Meta:
        model = CatalogItem
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "item_type",
            "item_type_display",
            "price",
            "currency",
            "tipo_filiacao",
            "anuidade_ano",
        ]


class CartItemSerializer(serializers.ModelSerializer):
    catalog_item = CatalogItemSerializer(read_only=True)
    catalog_item_id = serializers.UUIDField(write_only=True, required=False)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "catalog_item",
            "catalog_item_id",
            "quantity",
            "subtotal",
            "created_at",
        ]
        read_only_fields = ["id", "catalog_item", "subtotal", "created_at"]

    def get_subtotal(self, obj):
        return str(obj.get_subtotal())


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    membro_nome = serializers.CharField(source="membro.nome_completo", read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "membro_nome", "items", "total", "item_count", "updated_at"]
        read_only_fields = fields

    def get_total(self, obj):
        return str(obj.get_total())

    def get_item_count(self, obj):
        return obj.get_item_count()


class OrderItemSerializer(serializers.ModelSerializer):
    catalog_item_name = serializers.CharField(source="catalog_item.name", read_only=True)
    item_type_display = serializers.CharField(source="get_item_type_display", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "catalog_item",
            "catalog_item_name",
            "item_type",
            "item_type_display",
            "quantity",
            "price_at_purchase",
            "subtotal",
            "fulfillment_ref",
            "created_at",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True, allow_blank=True
    )
    membro_nome = serializers.CharField(source="membro.nome_completo", read_only=True, allow_null=True)
    membro_email = serializers.EmailField(source="membro.email", read_only=True, allow_null=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "membro",
            "membro_nome",
            "membro_email",
            "total_amount",
            "currency",
            "status",
            "status_display",
            "payment_method",
            "payment_method_display",
            "paid_at",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "order_number",
            "membro_nome",
            "membro_email",
            "total_amount",
            "paid_at",
            "items",
            "created_at",
            "updated_at",
        ]


class CheckoutSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    payment_method = serializers.ChoiceField(
        choices=["simulated", "manual"],
        default="simulated",
        required=False,
    )
