"""
Tarefas periódicas do servidor (serviço `agendador` do compose).

- A cada minuto: um lote da fila da newsletter (`enviar_newsletters`).
- Uma vez por dia, a partir de REGUA_HORA (horário de Brasília): a régua de anuidades
  (`regua_anuidades`), que marca vencidas/inadimplentes e envia os lembretes.

    docker compose exec -T backend python manage.py agendador
"""
import time

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

_BACKENDS_SEM_ENTREGA = {
    "django.core.mail.backends.console.EmailBackend",
    "django.core.mail.backends.locmem.EmailBackend",
    "django.core.mail.backends.dummy.EmailBackend",
    "django.core.mail.backends.filebased.EmailBackend",
}


def email_entregue() -> bool:
    return settings.EMAIL_BACKEND not in _BACKENDS_SEM_ENTREGA


class Command(BaseCommand):
    help = "Roda a fila da newsletter a cada minuto e a régua de anuidades uma vez por dia."

    def _rodar(self, nome, comando, *args) -> bool:
        try:
            call_command(comando, *args, stdout=self.stdout, stderr=self.stderr)
            return True
        except Exception as exc:
            self.stderr.write(f"Falha em {nome}: {exc}")
            return False

    def ciclo(self, agora=None):
        self._rodar("newsletter", "enviar_newsletters")

        agora = agora or timezone.localtime()
        if agora.hour < getattr(settings, "REGUA_HORA", 8) or self.ultima_regua == agora.date():
            return
        # Sem provedor que entregue de fato, o lembrete ficaria registrado como
        # enviado e a etapa nunca seria reenviada quando o e-mail passar a funcionar.
        extra = [] if email_entregue() else ["--sem-email"]
        self.stdout.write(f"Régua de anuidades {agora:%d/%m %H:%M}{' (sem e-mail)' if extra else ''}")
        if self._rodar("régua de anuidades", "regua_anuidades", *extra):
            self.ultima_regua = agora.date()

    def handle(self, *args, **options):
        self.ultima_regua = None
        while True:
            inicio = time.monotonic()
            self.ciclo()
            time.sleep(max(60 - (time.monotonic() - inicio), 1))
