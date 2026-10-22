"""
Consulta no gateway as cobranças online pendentes dos últimos dias e aplica pagamentos
e cancelamentos que não chegaram por webhook. O agendador roda a cada 30 minutos.

    docker compose exec -T backend python manage.py sincronizar_cobrancas [--schema abciber]
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django_tenants.utils import get_public_schema_name, tenant_context

from payments.services import sincronizar_pendentes
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Sincroniza o status das cobranças online pendentes com o gateway de cada associação."

    def add_arguments(self, parser):
        parser.add_argument("--schema", help="Rodar apenas para este schema")

    def handle(self, *args, **options):
        excluidos = {get_public_schema_name(), getattr(settings, "SYSTEM_TENANT_SCHEMA", "sistema")}
        tenants = Tenant.objects.filter(is_active=True).exclude(schema_name__in=excluidos)
        if options.get("schema"):
            tenants = tenants.filter(schema_name=options["schema"])

        for tenant in tenants:
            with tenant_context(tenant):
                contagem = sincronizar_pendentes()
            if any(contagem.values()):
                partes = " ".join(f"{k}={v}" for k, v in contagem.items())
                self.stdout.write(f"[{tenant.schema_name}] {partes}")
