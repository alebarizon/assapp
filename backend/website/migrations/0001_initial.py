import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="WebsiteConfig",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("site_title", models.CharField(default="Minha Associação", max_length=200)),
                ("site_tagline", models.CharField(blank=True, default="", max_length=300)),
                ("site_description", models.TextField(blank=True, default="")),
                ("primary_color", models.CharField(default="#1a5f4a", max_length=7)),
                ("secondary_color", models.CharField(default="#0f172a", max_length=7)),
                ("logo_url", models.URLField(blank=True, default="")),
                ("favicon_url", models.URLField(blank=True, default="")),
                ("hero_title", models.CharField(blank=True, default="", max_length=255)),
                ("hero_subtitle", models.TextField(blank=True, default="")),
                ("hero_image_url", models.URLField(blank=True, default="")),
                ("hero_cta_label", models.CharField(blank=True, default="Conheça a associação", max_length=80)),
                ("hero_cta_link", models.CharField(blank=True, default="#sobre", max_length=200)),
                ("about_title", models.CharField(blank=True, default="Sobre a associação", max_length=200)),
                ("about_text", models.TextField(blank=True, default="")),
                ("associe_se_title", models.CharField(default="Associe-se", max_length=200)),
                (
                    "associe_se_lead",
                    models.TextField(
                        blank=True,
                        default=(
                            "Apoie a pesquisa científica e associe-se. A filiação anual oferece "
                            "benefícios em eventos e na comunidade associativa."
                        ),
                    ),
                ),
                ("associe_se_categories", models.JSONField(blank=True, default=list)),
                ("associe_se_cta_label", models.CharField(default="Quero me associar", max_length=80)),
                ("associe_se_cta_link", models.CharField(default="/login", max_length=200)),
                ("contact_email", models.EmailField(blank=True, default="")),
                ("contact_phone", models.CharField(blank=True, default="", max_length=40)),
                ("contact_address", models.CharField(blank=True, default="", max_length=500)),
                ("social_links", models.JSONField(blank=True, default=list)),
                ("is_published", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuração do website",
                "verbose_name_plural": "Configurações do website",
            },
        ),
        migrations.CreateModel(
            name="SitePage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("summary", models.TextField(blank=True, default="")),
                ("content", models.TextField(blank=True, default="")),
                (
                    "page_type",
                    models.CharField(
                        choices=[("noticia", "Notícia"), ("institucional", "Institucional")],
                        db_index=True,
                        default="institucional",
                        max_length=20,
                    ),
                ),
                ("is_published", models.BooleanField(db_index=True, default=False)),
                ("is_featured", models.BooleanField(db_index=True, default=False)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Página do site",
                "verbose_name_plural": "Páginas do site",
                "ordering": ["order", "-published_at", "title"],
            },
        ),
    ]
