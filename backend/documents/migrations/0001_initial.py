# Documents initial migration
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("membros", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=200)),
                ("file", models.FileField(upload_to="documents/%Y/%m/%d/")),
                ("file_type", models.CharField(blank=True, max_length=50, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "audience",
                    models.CharField(
                        choices=[
                            ("geral", "Geral (associação)"),
                            ("diretoria", "Diretoria"),
                            ("membro", "Membro específico"),
                        ],
                        db_index=True,
                        default="geral",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "membro",
                    models.ForeignKey(
                        blank=True,
                        help_text="Obrigatório quando audience=membro",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="documents",
                        to="membros.membro",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="uploaded_documents",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Documento",
                "verbose_name_plural": "Documentos",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(fields=["audience", "created_at"], name="documents_d_audienc_idx"),
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(fields=["membro", "created_at"], name="documents_d_membro__idx"),
        ),
    ]
