"""
Tarefas periódicas do servidor (serviço `agendador` do compose).

- A cada minuto: um lote da fila da newsletter (`enviar_newsletters`).
- Uma vez por dia, a partir de REGUA_HORA (horário de Brasília):
  - régua de anuidades (`regua_anuidades`): marca vencidas/inadimplentes e envia os lembretes;
  - réguas de relacionamento (`reguas_relacionamento`): boas-vindas, inativos, autor não sócio.

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
    help = "Roda a fila da newsletter a cada minuto e as réguas diárias (anuidades e relacionamento)."

    def _rodar(self, nome, comando, *args) -> bool:
        try:
            call_command(comando, *args, stdout=self.stdout, stderr=self.stderr)
            return True
        except Exception as exc:
            self.stderr.write(f"Falha em {nome}: {exc}")
            return False

    def _diarias(self) -> list[tuple[str, str, list[str]]]:
        # Sem provedor que entregue de fato, o envio ficaria registrado como feito e
        # nunca seria repetido quando o e-mail passar a funcionar.
        if not email_entregue():
            return [("régua de anuidades", "regua_anuidades", ["--sem-email"])]
        return [
            ("régua de anuidades", "regua_anuidades", []),
            ("réguas de relacionamento", "reguas_relacionamento", []),
        ]

    def ciclo(self, agora=None):
        self._rodar("newsletter", "enviar_newsletters")

        agora = agora or timezone.localtime()
        if agora.hour < getattr(settings, "REGUA_HORA", 8):
            return
        for nome, comando, args in self._diarias():
            if self.ultimas.get(comando) == agora.date():
                continue
            self.stdout.write(f"{nome[0].upper()}{nome[1:]} {agora:%d/%m %H:%M}{' (sem e-mail)' if args else ''}")
            if self._rodar(nome, comando, *args):
                self.ultimas[comando] = agora.date()

    def handle(self, *args, **options):
        self.ultimas = {}
        while True:
            inicio = time.monotonic()
            self.ciclo()
            time.sleep(max(60 - (time.monotonic() - inicio), 1))
