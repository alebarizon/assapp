"""
Envio de e-mails transacionais.

Falhas de SMTP nunca derrubam a requisição: são registradas em log e a função
retorna False, para que o fluxo principal (inscrição, convite, contato) siga.
A mensagem que falhou vai para `EmailPendente` e o agendador tenta de novo
(`reenviar_emails`), com intervalo crescente, por até ~24 h.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.utils import timezone
from django.utils.html import escape, linebreaks
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)

ESPERAS_MINUTOS = [5, 15, 30, 60, 120, 240, 480, 720]
CACHE_SMTP = "core:smtp_disponivel"


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


def _enfileirar(email: EmailMultiAlternatives, html: str, erro: Exception) -> None:
    from django.db import connection

    from core.models import EmailPendente

    try:
        EmailPendente.objects.create(
            schema=getattr(connection, "schema_name", "") or "",
            remetente=email.from_email,
            destinatarios=list(email.to),
            reply_to=list(email.reply_to or []),
            assunto=email.subject[:255],
            texto=email.body,
            html=html,
            ultimo_erro=str(erro)[:500],
            proxima_tentativa=timezone.now() + timedelta(minutes=ESPERAS_MINUTOS[0]),
        )
    except Exception:
        logger.exception("Falha ao guardar e-mail '%s' para reenvio", email.subject)


def enviar_email(
    destinatarios,
    assunto: str,
    texto: str,
    link: str | None = None,
    link_label: str = "Acessar",
    reply_to: str | None = None,
    fila: bool = True,
) -> bool:
    """`fila=False` para quem já repete o envio sozinho (ex.: régua de anuidades), evitando duplicar."""
    if isinstance(destinatarios, str):
        destinatarios = [destinatarios]
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        return False
    mensagem = f"{texto}\n\n{link}" if link else texto
    html = _html(texto, link, link_label)
    email = EmailMultiAlternatives(
        subject=assunto,
        body=mensagem,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=destinatarios,
        reply_to=[reply_to] if reply_to else None,
    )
    email.attach_alternative(html, "text/html")
    try:
        email.send()
        return True
    except Exception as exc:
        logger.exception("Falha ao enviar e-mail '%s' para %s", assunto, destinatarios)
        if fila:
            _enfileirar(email, html, exc)
        return False


def usa_smtp() -> bool:
    try:
        return issubclass(import_string(settings.EMAIL_BACKEND), SMTPBackend)
    except ImportError:
        return False


def smtp_disponivel(usar_cache: bool = True) -> bool | None:
    """Abre e fecha uma conexão (com login) no SMTP. None quando o backend não é SMTP."""
    if not usa_smtp():
        return None
    if usar_cache:
        guardado = cache.get(CACHE_SMTP)
        if guardado is not None:
            return guardado
    conexao = get_connection(timeout=8)
    try:
        conexao.open()
        ok = True
    except Exception as exc:
        logger.warning("SMTP indisponível: %s", exc)
        ok = False
    finally:
        try:
            conexao.close()
        except Exception:
            pass
    cache.set(CACHE_SMTP, ok, 60)
    return ok


def reenviar_pendentes(limite: int = 50) -> dict:
    """Tenta de novo os e-mails individuais que falharam. Sem SMTP, não gasta tentativas."""
    from core.models import EmailPendente

    agora = timezone.now()
    lote = list(
        EmailPendente.objects.filter(status=EmailPendente.PENDENTE, proxima_tentativa__lte=agora)[:limite]
    )
    resultado = {"enviados": 0, "falhas": 0, "desistencias": 0}
    if not lote:
        return resultado

    conexao = get_connection()
    try:
        conexao.open()
    except Exception as exc:
        logger.warning("Reenvio de e-mails adiado: SMTP indisponível (%s)", exc)
        return resultado

    try:
        for pendente in lote:
            email = EmailMultiAlternatives(
                subject=pendente.assunto,
                body=pendente.texto,
                from_email=pendente.remetente,
                to=pendente.destinatarios,
                reply_to=pendente.reply_to or None,
                connection=conexao,
            )
            if pendente.html:
                email.attach_alternative(pendente.html, "text/html")
            try:
                email.send()
            except Exception as exc:
                pendente.tentativas += 1
                pendente.ultimo_erro = str(exc)[:500]
                if pendente.tentativas > len(ESPERAS_MINUTOS):
                    pendente.status = EmailPendente.DESISTIU
                    resultado["desistencias"] += 1
                    logger.error("Desistindo do e-mail '%s' para %s: %s", pendente.assunto, pendente.destinatarios, exc)
                else:
                    espera = ESPERAS_MINUTOS[pendente.tentativas - 1]
                    pendente.proxima_tentativa = agora + timedelta(minutes=espera)
                    resultado["falhas"] += 1
            else:
                pendente.status = EmailPendente.ENVIADO
                pendente.enviado_em = timezone.now()
                resultado["enviados"] += 1
            pendente.save(update_fields=["status", "tentativas", "ultimo_erro", "proxima_tentativa", "enviado_em"])
    finally:
        conexao.close()

    EmailPendente.objects.filter(
        status__in=[EmailPendente.ENVIADO, EmailPendente.DESISTIU], criado_em__lt=agora - timedelta(days=30)
    ).delete()
    return resultado
