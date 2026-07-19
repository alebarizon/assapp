# Finance initial migration
import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("mandatos", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("description", models.CharField(max_length=255)),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0.01)],
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("income", "Receita"), ("expense", "Despesa")],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("category", models.CharField(db_index=True, max_length=50)),
                ("occurred_at", models.DateTimeField(db_index=True)),
                (
                    "referencia",
                    models.CharField(
                        blank=True,
                        help_text="Ex: anuidade:<uuid>",
                        max_length=100,
                        null=True,
                        unique=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "mandato",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transactions",
                        to="mandatos.mandato",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        help_text="Usuário que lançou (auditoria)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transactions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Transação",
                "verbose_name_plural": "Transações",
                "ordering": ["-occurred_at", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["type", "occurred_at"], name="finance_tra_type_oc_idx"),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["category", "occurred_at"], name="finance_tra_categor_idx"),
        ),
    ]
