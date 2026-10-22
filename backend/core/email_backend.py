from django.core.mail.backends.smtp import EmailBackend

from core import cota_email


class CotaSMTPBackend(EmailBackend):
    """SMTP que registra cada mensagem entregue na cota horária (`core.cota_email`)."""

    def _send(self, email_message):
        enviado = super()._send(email_message)
        if enviado:
            cota_email.registrar(len(email_message.recipients()))
        return enviado
