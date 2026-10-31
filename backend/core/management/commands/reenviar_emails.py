from django.core.management.base import BaseCommand

from core.emails import reenviar_pendentes


class Command(BaseCommand):
    help = "Tenta de novo os e-mails individuais que falharam (core.EmailPendente)."

    def handle(self, *args, **options):
        resultado = reenviar_pendentes()
        if any(resultado.values()):
            self.stdout.write(
                f"Reenvio de e-mails: {resultado['enviados']} enviados, {resultado['falhas']} falharam de novo, "
                f"{resultado['desistencias']} desistências"
            )
