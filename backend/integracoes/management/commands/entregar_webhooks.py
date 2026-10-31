"""
Entrega os webhooks de saída pendentes de todas as associações (o agendador chama a cada minuto).

    docker compose exec -T backend python manage.py entregar_webhooks
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_tenants.utils import get_public_schema_name, tenant_context

from integracoes.models import EntregaWebhook
from integracoes.services import processar_fila
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Entrega os webhooks de saída pendentes."

    def add_arguments(self, parser):
        parser.add_argument("--schema", help="Rodar apenas para este schema")

    def handle(self, *args, **options):
        excluidos = {get_public_schema_name(), getattr(settings, "SYSTEM_TENANT_SCHEMA", "sistema")}
        tenants = Tenant.objects.filter(is_active=True).exclude(schema_name__in=excluidos)
        if options.get("schema"):
            tenants = tenants.filter(schema_name=options["schema"])
        for tenant in tenants:
            with tenant_context(tenant):
                pendentes = EntregaWebhook.objects.filter(
                    status=EntregaWebhook.PENDENTE, proxima_tentativa__lte=timezone.now(), webhook__ativo=True
                )
                if not pendentes.exists():
                    continue
                r = processar_fila()
            self.stdout.write(f"[{tenant.schema_name}] webhooks entregues={r['entregues']} falhas={r['falhas']}")
