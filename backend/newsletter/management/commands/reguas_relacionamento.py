"""
Réguas de relacionamento (boas-vindas, inativos, autor não sócio) em todas as
associações, ou em uma com --schema. O agendador roda uma vez por dia.

    docker compose exec -T backend python manage.py reguas_relacionamento
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django_tenants.utils import get_public_schema_name, tenant_context

from newsletter.reguas import executar
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Envia as réguas automáticas de relacionamento ativas em cada associação."

    def add_arguments(self, parser):
        parser.add_argument("--schema", help="Rodar apenas para este schema")

    def handle(self, *args, **options):
        excluidos = {get_public_schema_name(), getattr(settings, "SYSTEM_TENANT_SCHEMA", "sistema")}
        tenants = Tenant.objects.filter(is_active=True).exclude(schema_name__in=excluidos)
        if options.get("schema"):
            tenants = tenants.filter(schema_name=options["schema"])

        for tenant in tenants:
            with tenant_context(tenant):
                resultado = executar()
            partes = [f"{tipo}={r['enviados']}" + (f"/falhas={r['falhas']}" if r["falhas"] else "")
                      for tipo, r in resultado.items()]
            self.stdout.write(f"[{tenant.schema_name}] " + (" ".join(partes) or "nenhuma régua ativa"))
