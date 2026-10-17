"""
Envio de e-mails transacionais.

Falhas de SMTP nunca derrubam a requisição: são registradas em log e a função
retorna False, para que o fluxo principal (inscrição, convite, contato) siga.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import escape, linebreaks

logger = logging.getLogger(__name__)


def nome_associacao(request=None) -> str:
    from django.db import connection

    user = getattr(request, "user", None)
    tenant = getattr(user, "_tenant", None) or getattr(connection, "tenant", None)
    return getattr(tenant, "name", "") or "A associação"


def frontend_url(path: str = "") -> str:
    base = getattr(settings, "FRONTEND_URL", "") or "http://localhost:5174"
    return f"{base.rstrip('/')}/{path.lstrip('/')}" if path else base.rstrip("/")


def _html(texto: str, link: str | None, link_label: str) -> str:
    corpo = linebreaks(escape(texto))
    botao = ""
    if link:
        botao = (
            f'<p style="margin-top:24px"><a href="{escape(link)}" '
            'style="background:#1a5f4a;color:#fff;padding:10px 18px;border-radius:6px;'
            f'text-decoration:none">{escape(link_label)}</a></p>'
            f'<p style="color:#64748b;font-size:12px">Ou copie o endereço: {escape(link)}</p>'
        )
    return f'<div style="font-family:Arial,sans-serif;font-size:15px;color:#0f172a">{corpo}{botao}</div>'


def enviar_email(
    destinatarios,
    assunto: str,
    texto: str,
    link: str | None = None,
    link_label: str = "Acessar",
    reply_to: str | None = None,
) -> bool:
    if isinstance(destinatarios, str):
        destinatarios = [destinatarios]
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        return False
    mensagem = f"{texto}\n\n{link}" if link else texto
    try:
        email = EmailMultiAlternatives(
            subject=assunto,
            body=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios,
            reply_to=[reply_to] if reply_to else None,
        )
        email.attach_alternative(_html(texto, link, link_label), "text/html")
        email.send()
        return True
    except Exception:
        logger.exception("Falha ao enviar e-mail '%s' para %s", assunto, destinatarios)
        return False
