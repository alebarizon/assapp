"""
Régua diária de anuidades em todas as associações (ou em uma, com --schema).

Marca vencidas/inadimplentes e envia o lembrete devido de cada anuidade em aberto.
Em staging e produção o serviço `agendador` do compose roda uma vez por dia. À mão:

    docker compose exec -T backend python manage.py regua_anuidades
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django_tenants.utils import get_public_schema_name, tenant_context

from membros.services import atualizar_anuidades_vencidas, enviar_lembretes_anuidade
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Atualiza anuidades vencidas e envia lembretes de cobrança aos associados."

    def add_arguments(self, parser):
        parser.add_argument("--schema", help="Rodar apenas para este schema")
        parser.add_argument(
            "--sem-email",
            action="store_true",
            help="Só atualiza vencidas, sem enviar lembretes",
        )

    def handle(self, *args, **options):
        excluidos = {get_public_schema_name(), getattr(settings, "SYSTEM_TENANT_SCHEMA", "sistema")}
        tenants = Tenant.objects.filter(is_active=True).exclude(schema_name__in=excluidos)
        if options.get("schema"):
            tenants = tenants.filter(schema_name=options["schema"])

        for tenant in tenants:
            with tenant_context(tenant):
                vencidas = atualizar_anuidades_vencidas()
                linha = (
                    f"[{tenant.schema_name}] vencidas={vencidas['anuidades_vencidas']} "
                    f"inadimplentes={vencidas['filiacoes_inadimplentes']}"
                )
                if not options.get("sem_email"):
                    lembretes = enviar_lembretes_anuidade()
                    linha += f" lembretes={lembretes['enviados']} falhas={lembretes['falhas']}"
            self.stdout.write(linha)
