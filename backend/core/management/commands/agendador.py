"""
Tarefas periódicas do servidor (serviço `agendador` do compose).

- A cada minuto: um lote da fila da newsletter (`enviar_newsletters`) e o reenvio dos
  e-mails individuais que falharam (`reenviar_emails`); webhooks de saída (`entregar_webhooks`).
- A cada 30 minutos: status das cobranças online pendentes (`sincronizar_cobrancas`).
- Uma vez por dia, a partir de REGUA_HORA (horário de Brasília):
  - régua de anuidades (`regua_anuidades`): marca vencidas/inadimplentes e envia os lembretes;
  - réguas de relacionamento (`reguas_relacionamento`): boas-vindas, inativos, autor não sócio.
  Com o SMTP fora do ar, as diárias esperam e são tentadas de novo no minuto seguinte.

    docker compose exec -T backend python manage.py agendador
"""
import time
from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.emails import smtp_disponivel

_BACKENDS_SEM_ENTREGA = {
    "django.core.mail.backends.console.EmailBackend",
    "django.core.mail.backends.locmem.EmailBackend",
    "django.core.mail.backends.dummy.EmailBackend",
    "django.core.mail.backends.filebased.EmailBackend",
}
INTERVALO_COBRANCAS = timedelta(minutes=30)


def email_entregue() -> bool:
    return settings.EMAIL_BACKEND not in _BACKENDS_SEM_ENTREGA


class Command(BaseCommand):
    help = (
        "Roda a fila da newsletter a cada minuto, a sincronização de cobranças a cada 30 minutos "
        "e as réguas diárias (anuidades e relacionamento)."
    )

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

    def _smtp_ok(self) -> bool:
        ok = smtp_disponivel() is not False
        if ok != self.ultimas.get("smtp_ok", True):
            self.stderr.write("SMTP voltou." if ok else "SMTP indisponível: tarefas diárias de e-mail adiadas.")
        self.ultimas["smtp_ok"] = ok
        return ok

    def ciclo(self, agora=None):
        self._rodar("newsletter", "enviar_newsletters")
        if email_entregue():
            self._rodar("reenvio de e-mails", "reenviar_emails")
        self._rodar("webhooks de saída", "entregar_webhooks")

        agora = agora or timezone.localtime()
        ultima = self.ultimas.get("sincronizar_cobrancas")
        if ultima is None or agora - ultima >= INTERVALO_COBRANCAS:
            self._rodar("cobranças online", "sincronizar_cobrancas")
            self.ultimas["sincronizar_cobrancas"] = agora

        if agora.hour < getattr(settings, "REGUA_HORA", 8):
            return
        pendentes = [d for d in self._diarias() if self.ultimas.get(d[1]) != agora.date()]
        if pendentes and email_entregue() and not self._smtp_ok():
            return
        for nome, comando, args in pendentes:
            self.stdout.write(f"{nome[0].upper()}{nome[1:]} {agora:%d/%m %H:%M}{' (sem e-mail)' if args else ''}")
            if self._rodar(nome, comando, *args):
                self.ultimas[comando] = agora.date()

    def handle(self, *args, **options):
        self.ultimas = {}
        while True:
            inicio = time.monotonic()
            self.ciclo()
            time.sleep(max(60 - (time.monotonic() - inicio), 1))
