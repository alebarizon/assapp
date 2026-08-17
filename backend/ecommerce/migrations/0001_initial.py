# E-commerce Gesttora — catálogo, carrinho e pedidos
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("eventos", "0001_initial"),
        ("membros", "0002_membro_user_link"),
    ]

    operations = [
        migrations.CreateModel(
            name="CatalogItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=200)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "item_type",
                    models.CharField(
                        choices=[
                            ("anuidade", "Anuidade"),
                            ("inscricao", "Inscrição em evento"),
                            ("curso", "Curso / workshop"),
                            ("material", "Material físico"),
                            ("digital", "Conteúdo digital"),
                        ],
                        db_index=True,
                        default="material",
                        max_length=20,
                    ),
                ),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(default="BRL", max_length=3)),
                ("inventory_count", models.PositiveIntegerField(blank=True, null=True)),
                ("image_url", models.URLField(blank=True, null=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("anuidade_ano", models.PositiveIntegerField(blank=True, null=True)),
                ("tipo_filiacao", models.CharField(blank=True, max_length=20, null=True)),
                ("metadata", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="catalog_items_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "evento",
                    models.ForeignKey(
                        blank=True,
                        help_text="Evento vinculado quando item_type=inscricao",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="catalog_items",
                        to="eventos.eventoacademico",
                    ),
                ),
            ],
            options={
                "verbose_name": "Item do catálogo",
                "verbose_name_plural": "Itens do catálogo",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("order_number", models.CharField(db_index=True, max_length=50, unique=True)),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(default="BRL", max_length=3)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("paid", "Pago"),
                            ("fulfilled", "Concluído"),
                            ("cancelled", "Cancelado"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "payment_method",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("simulated", "Simulado (dev)"),
                            ("manual", "Manual / transferência"),
                            ("stripe", "Stripe"),
                        ],
                        default="",
                        max_length=20,
                    ),
                ),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("stripe_payment_intent_id", models.CharField(blank=True, max_length=255, null=True)),
                ("notes", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "membro",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="orders",
                        to="membros.membro",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pedido",
                "verbose_name_plural": "Pedidos",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Cart",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "membro",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cart",
                        to="membros.membro",
                    ),
                ),
            ],
            options={
                "verbose_name": "Carrinho",
                "verbose_name_plural": "Carrinhos",
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "item_type",
                    models.CharField(
                        choices=[
                            ("anuidade", "Anuidade"),
                            ("inscricao", "Inscrição em evento"),
                            ("curso", "Curso / workshop"),
                            ("material", "Material físico"),
                            ("digital", "Conteúdo digital"),
                        ],
                        max_length=20,
                    ),
                ),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("price_at_purchase", models.DecimalField(decimal_places=2, max_digits=10)),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=10)),
                ("fulfillment_ref", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "catalog_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_items",
                        to="ecommerce.catalogitem",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="ecommerce.order",
                    ),
                ),
            ],
            options={
                "verbose_name": "Item do pedido",
                "verbose_name_plural": "Itens do pedido",
            },
        ),
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "cart",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="ecommerce.cart",
                    ),
                ),
                (
                    "catalog_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cart_items",
                        to="ecommerce.catalogitem",
                    ),
                ),
            ],
            options={
                "verbose_name": "Item do carrinho",
                "verbose_name_plural": "Itens do carrinho",
            },
        ),
        migrations.AddIndex(
            model_name="catalogitem",
            index=models.Index(fields=["is_active", "item_type"], name="ecommerce_c_is_acti_idx"),
        ),
        migrations.AddIndex(
            model_name="catalogitem",
            index=models.Index(fields=["slug"], name="ecommerce_c_slug_idx"),
        ),
        migrations.AddConstraint(
            model_name="catalogitem",
            constraint=models.UniqueConstraint(fields=("slug",), name="unique_catalog_item_slug"),
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(
                fields=("cart", "catalog_item"), name="unique_catalog_item_per_cart"
            ),
        ),
    ]
