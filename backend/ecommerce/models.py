"""
Gesttora — Catálogo unificado de ofertas (anuidade, inscrição, curso, material).

Adaptado do motor WellSaaS (Product/Cart/Order), com tipos de item e comprador Membro.
"""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class CatalogItemType(models.TextChoices):
    ANUIDADE = "anuidade", "Anuidade"
    INSCRICAO = "inscricao", "Inscrição em evento"
    CURSO = "curso", "Curso / workshop"
    MATERIAL = "material", "Material físico"
    DIGITAL = "digital", "Conteúdo digital"


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    PAID = "paid", "Pago"
    FULFILLED = "fulfilled", "Concluído"
    CANCELLED = "cancelled", "Cancelado"


class PaymentMethod(models.TextChoices):
    SIMULATED = "simulated", "Simulado (dev)"
    MANUAL = "manual", "Manual / transferência"
    STRIPE = "stripe", "Stripe"


class CatalogItem(models.Model):
    """Item vendável no catálogo da associação."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, db_index=True)
    description = models.TextField(blank=True, null=True)
    item_type = models.CharField(
        max_length=20,
        choices=CatalogItemType.choices,
        default=CatalogItemType.MATERIAL,
        db_index=True,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="BRL")
    inventory_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Obrigatório para materiais físicos; null = ilimitado",
    )
    image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    # Metadados por tipo
    anuidade_ano = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Ano de referência quando item_type=anuidade",
    )
    tipo_filiacao = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Tipo de filiação coberto (anuidade); vazio = qualquer",
    )
    evento = models.ForeignKey(
        "eventos.EventoAcademico",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="catalog_items",
        help_text="Evento vinculado quando item_type=inscricao",
    )
    metadata = models.JSONField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="catalog_items_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item do catálogo"
        verbose_name_plural = "Itens do catálogo"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "item_type"]),
            models.Index(fields=["slug"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["slug"], name="unique_catalog_item_slug"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "item"
            slug = base
            n = 1
            while CatalogItem.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        if self.price is not None and self.price < 0:
            raise ValidationError({"price": "Preço não pode ser negativo."})
        if self.item_type == CatalogItemType.ANUIDADE and not self.anuidade_ano:
            raise ValidationError({"anuidade_ano": "Informe o ano da anuidade."})
        if self.item_type == CatalogItemType.INSCRICAO and not self.evento_id:
            raise ValidationError({"evento": "Vincule um evento para inscrições."})
        if self.item_type == CatalogItemType.MATERIAL and self.inventory_count is None:
            raise ValidationError(
                {"inventory_count": "Materiais físicos exigem controle de estoque."}
            )


class Cart(models.Model):
    """Carrinho 1:1 com Membro."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membro = models.OneToOneField(
        "membros.Membro",
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carrinho"
        verbose_name_plural = "Carrinhos"

    def __str__(self):
        return f"Carrinho — {self.membro.nome_completo}"

    def get_total(self):
        total = 0
        for item in self.items.select_related("catalog_item"):
            total += item.get_subtotal()
        return total

    def get_item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    catalog_item = models.ForeignKey(
        CatalogItem,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item do carrinho"
        verbose_name_plural = "Itens do carrinho"
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "catalog_item"],
                name="unique_catalog_item_per_cart",
            )
        ]

    def __str__(self):
        return f"{self.catalog_item.name} x{self.quantity}"

    def get_subtotal(self):
        return self.quantity * self.catalog_item.price

    def clean(self):
        if self.catalog_item_id and not self.catalog_item.is_active:
            raise ValidationError("Item indisponível no catálogo.")
        if self.catalog_item.inventory_count is not None:
            if self.catalog_item.inventory_count < self.quantity:
                raise ValidationError("Estoque insuficiente.")


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membro = models.ForeignKey(
        "membros.Membro",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="BRL")
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
        default="",
    )
    paid_at = models.DateTimeField(blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Pedido {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            from django.utils import timezone
            import random
            import string

            now = timezone.now()
            rnd = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            self.order_number = f"PED-{now.strftime('%Y%m%d%H%M%S')}-{rnd}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    catalog_item = models.ForeignKey(
        CatalogItem,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    item_type = models.CharField(max_length=20, choices=CatalogItemType.choices)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    fulfillment_ref = models.JSONField(
        blank=True,
        null=True,
        help_text='Ex: {"type":"anuidade","id":"uuid"} após pagamento',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item do pedido"
        verbose_name_plural = "Itens do pedido"

    def __str__(self):
        return f"{self.catalog_item.name} — {self.order.order_number}"
