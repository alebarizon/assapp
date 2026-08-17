"""
Website público da associação (tenant) — CMS Gesttora.

Escopo comercial: identidade, notícias, instituição, box Associe-se, contato.
Sites de Evento, Publicações, Certificados etc. são produtos/módulos futuros.
"""
import uuid

from django.db import models


class PageType(models.TextChoices):
    NOTICIA = "noticia", "Notícia"
    INSTITUCIONAL = "institucional", "Institucional"


class WebsiteConfig(models.Model):
    """Configuração singleton do site (um registro por schema tenant)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site_title = models.CharField(max_length=200, default="Minha Associação")
    site_tagline = models.CharField(max_length=300, blank=True, default="")
    site_description = models.TextField(blank=True, default="")
    primary_color = models.CharField(max_length=7, default="#1a5f4a")
    secondary_color = models.CharField(max_length=7, default="#0f172a")
    logo_url = models.URLField(blank=True, default="")
    favicon_url = models.URLField(blank=True, default="")

    hero_title = models.CharField(max_length=255, blank=True, default="")
    hero_subtitle = models.TextField(blank=True, default="")
    hero_image_url = models.URLField(blank=True, default="")
    hero_cta_label = models.CharField(max_length=80, blank=True, default="Conheça a associação")
    hero_cta_link = models.CharField(max_length=200, blank=True, default="#sobre")

    about_title = models.CharField(max_length=200, blank=True, default="Sobre a associação")
    about_text = models.TextField(blank=True, default="")

    # Box Associe-se (referência de UX — categorias de filiação)
    associe_se_title = models.CharField(max_length=200, default="Associe-se")
    associe_se_lead = models.TextField(
        blank=True,
        default=(
            "Apoie a pesquisa científica e associe-se. A filiação anual oferece "
            "benefícios em eventos e na comunidade associativa."
        ),
    )
    associe_se_categories = models.JSONField(
        default=list,
        blank=True,
        help_text='[{"label":"Alunos de Graduação","hint":"Valores reduzidos"}, ...]',
    )
    associe_se_cta_label = models.CharField(max_length=80, default="Quero me associar")
    associe_se_cta_link = models.CharField(
        max_length=200,
        default="auto:loja",
        help_text="Use auto:loja para login com redirect à loja do portal.",
    )

    contact_email = models.EmailField(blank=True, default="")
    contact_phone = models.CharField(max_length=40, blank=True, default="")
    contact_address = models.CharField(max_length=500, blank=True, default="")
    social_links = models.JSONField(default=list, blank=True)

    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração do website"
        verbose_name_plural = "Configurações do website"

    def __str__(self):
        return self.site_title


class SitePage(models.Model):
    """Páginas e notícias publicadas no site."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    summary = models.TextField(blank=True, default="")
    content = models.TextField(blank=True, default="")
    page_type = models.CharField(
        max_length=20,
        choices=PageType.choices,
        default=PageType.INSTITUCIONAL,
        db_index=True,
    )
    is_published = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Página do site"
        verbose_name_plural = "Páginas do site"
        ordering = ["order", "-published_at", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        from django.utils.text import slugify

        if not self.slug:
            base = slugify(self.title) or "pagina"
            slug = base
            n = 1
            while SitePage.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)
