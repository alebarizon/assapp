"""Modelos de multi-tenancy — uma associação por schema PostgreSQL."""
import uuid

from django.db import models
from django.utils.text import slugify
from django_tenants.models import DomainMixin, TenantMixin


class Tenant(TenantMixin):
    """Associação científica (tenant isolado por schema)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    schema_name = models.CharField(max_length=63)
    owner_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID do administrador da associação (schema do tenant)",
    )
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    on_trial = models.BooleanField(default=True)
    paid_until = models.DateField(null=True, blank=True)
    # Fase ①/② — signup + setup pós-compra (FLUXO_ASSINATURA_SETUP_TRANSICAO)
    setup_completed = models.BooleanField(
        default=False,
        help_text="True após wizard de setup (1º mandato + diretoria).",
    )
    plan_slug = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Plano SaaS escolhido no signup (ex: starter, profissional).",
    )
    payment_simulated = models.BooleanField(
        default=True,
        help_text="True quando o signup não passou por Stripe (modo simulado).",
    )
    logo = models.ImageField(upload_to="tenants/logos/%Y/%m/", blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    auto_create_schema = True
    auto_drop_schema = False

    class Meta:
        verbose_name = "Associação"
        verbose_name_plural = "Associações"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.schema_name:
            self.schema_name = self.slug
        super().save(*args, **kwargs)


class Domain(DomainMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.CharField(max_length=253, unique=True, db_index=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="domains")
    is_primary = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Domínio"
        verbose_name_plural = "Domínios"
        ordering = ["-is_primary", "domain"]

    def __str__(self):
        return self.domain
