from django.contrib import admin

from .models import Cart, CartItem, CatalogItem, Order, OrderItem


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ("name", "item_type", "price", "is_active", "anuidade_ano")
    list_filter = ("item_type", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("fulfillment_ref",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "membro", "total_amount", "status", "paid_at")
    list_filter = ("status", "payment_method")
    search_fields = ("order_number", "membro__nome_completo", "membro__email")
    inlines = [OrderItemInline]


admin.site.register(Cart)
admin.site.register(CartItem)
