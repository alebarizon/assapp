"""
Despacha a fila da newsletter de todas as associações (ou de uma, com --schema).

O limite por minuto vale para o servidor inteiro e é dividido entre as associações
com campanha em andamento. Com --loop o comando fica rodando (serviço `newsletter`
do compose); sem ele, processa um lote e sai (cron a cada minuto).

    docker compose exec -T backend python manage.py enviar_newsletters
"""
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django_tenants.utils import get_public_schema_name, tenant_context

from newsletter.models import Campanha, StatusCampanha
from newsletter.services import processar_fila
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Envia os e-mails pendentes das campanhas de newsletter, respeitando o limite por minuto."

    def add_arguments(self, parser):
        parser.add_argument("--schema", help="Rodar apenas para este schema")
        parser.add_argument("--por-minuto", type=int, default=None, help="Limite de e-mails por minuto")
        parser.add_argument("--loop", action="store_true", help="Não sair: processar um lote por minuto")

    def _tenants(self, schema):
        excluidos = {get_public_schema_name(), getattr(settings, "SYSTEM_TENANT_SCHEMA", "sistema")}
        qs = Tenant.objects.filter(is_active=True).exclude(schema_name__in=excluidos)
        return qs.filter(schema_name=schema) if schema else qs

    def _ciclo(self, schema, limite):
        ativos = []
        for tenant in self._tenants(schema):
            with tenant_context(tenant):
                if Campanha.objects.filter(status=StatusCampanha.ENVIANDO).exists():
                    ativos.append(tenant)
        if not ativos:
            return
        restante = limite
        cota = max(limite // len(ativos), 1)
        for tenant in ativos:
            if restante <= 0:
                break
            with tenant_context(tenant):
                r = processar_fila(min(cota, restante))
            restante -= r["processados"]
            self.stdout.write(f"[{tenant.schema_name}] enviados={r['enviados']} falhas={r['falhas']}")

    def handle(self, *args, **options):
        limite = options.get("por_minuto") or getattr(settings, "NEWSLETTER_POR_MINUTO", 30)
        if not options.get("loop"):
            self._ciclo(options.get("schema"), limite)
            return
        while True:
            inicio = time.monotonic()
            try:
                self._ciclo(options.get("schema"), limite)
            except Exception as exc:
                self.stderr.write(f"Falha no ciclo da newsletter: {exc}")
            time.sleep(max(60 - (time.monotonic() - inicio), 1))
