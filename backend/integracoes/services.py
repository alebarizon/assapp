"""
Webhooks de saída: eventos internos viram entregas HTTP assinadas para os endereços da associação.

`disparar` só grava a entrega (nunca derruba o fluxo que a chamou); o agendador entrega
(`entregar_webhooks`) e tenta de novo com intervalo crescente.

Corpo: {"id", "evento", "criado_em", "associacao", "dados"}. Cabeçalhos:
X-Gesttora-Evento, X-Gesttora-Entrega, X-Gesttora-Timestamp e
X-Gesttora-Assinatura = "sha256=" + HMAC-SHA256(segredo, f"{timestamp}.{corpo}").
"""
import hashlib
import hmac
import ipaddress
import json
import logging
import socket
import time
from datetime import timedelta
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from .models import EVENTO_TESTE, EntregaWebhook, WebhookSaida

logger = logging.getLogger(__name__)

ESPERAS_MINUTOS = [1, 5, 15, 60, 240, 720]
TIMEOUT = 10


class UrlBloqueada(ValueError):
    pass


def validar_url(url: str) -> None:
    """Só endereços públicos: o servidor não pode ser usado para alcançar a rede interna."""
    partes = urlparse(url)
    esquemas = {"https", "http"} if settings.DEBUG else {"https"}
    if partes.scheme not in esquemas:
        raise UrlBloqueada("Use um endereço https://.")
    if not partes.hostname:
        raise UrlBloqueada("Endereço inválido.")
    try:
        enderecos = socket.getaddrinfo(partes.hostname, partes.port or 443, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError):
        raise UrlBloqueada("Não foi possível encontrar esse endereço.")
    for *_, sockaddr in enderecos:
        ip = ipaddress.ip_address(sockaddr[0])
        if not ip.is_global or ip.is_multicast:
            raise UrlBloqueada("Endereços de rede interna não são permitidos.")


def disparar(evento: str, dados: dict) -> int:
    try:
        with transaction.atomic():
            agora = timezone.now()
            alvos = [w for w in WebhookSaida.objects.filter(ativo=True) if evento in (w.eventos or [])]
            EntregaWebhook.objects.bulk_create(
                [EntregaWebhook(webhook=w, evento=evento, dados=dados, proxima_tentativa=agora) for w in alvos]
            )
            return len(alvos)
    except Exception:
        logger.exception("Falha ao enfileirar webhooks do evento %s", evento)
        return 0


def assinar(segredo: str, timestamp: str, corpo: bytes) -> str:
    mensagem = timestamp.encode() + b"." + corpo
    return "sha256=" + hmac.new(segredo.encode(), mensagem, hashlib.sha256).hexdigest()


def _corpo(entrega: EntregaWebhook) -> bytes:
    return json.dumps(
        {
            "id": str(entrega.id),
            "evento": entrega.evento,
            "criado_em": entrega.created_at.isoformat(),
            "associacao": getattr(connection, "schema_name", ""),
            "dados": entrega.dados,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()


def _postar(webhook: WebhookSaida, entrega: EntregaWebhook) -> tuple[bool, int | None, str]:
    try:
        validar_url(webhook.url)
    except UrlBloqueada as exc:
        return False, None, str(exc)
    corpo = _corpo(entrega)
    timestamp = str(int(time.time()))
    try:
        resposta = requests.post(
            webhook.url,
            data=corpo,
            timeout=TIMEOUT,
            allow_redirects=False,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Gesttora-Webhooks/1.0",
                "X-Gesttora-Evento": entrega.evento,
                "X-Gesttora-Entrega": str(entrega.id),
                "X-Gesttora-Timestamp": timestamp,
                "X-Gesttora-Assinatura": assinar(webhook.segredo, timestamp, corpo),
            },
        )
    except requests.RequestException as exc:
        return False, None, f"{type(exc).__name__}: {exc}"[:500]
    if 200 <= resposta.status_code < 300:
        return True, resposta.status_code, ""
    return False, resposta.status_code, f"HTTP {resposta.status_code}: {resposta.text[:300]}"


def entregar(entrega: EntregaWebhook) -> bool:
    webhook = entrega.webhook
    ok, codigo, erro = _postar(webhook, entrega)
    agora = timezone.now()
    entrega.tentativas += 1
    entrega.resposta_status = codigo
    entrega.ultimo_erro = erro
    if ok:
        entrega.status = EntregaWebhook.ENTREGUE
        entrega.entregue_em = agora
        webhook.falhas_seguidas = 0
        webhook.ultima_entrega_em = agora
    else:
        webhook.falhas_seguidas += 1
        if entrega.evento == EVENTO_TESTE or entrega.tentativas > len(ESPERAS_MINUTOS):
            entrega.status = EntregaWebhook.DESISTIU
        else:
            entrega.proxima_tentativa = agora + timedelta(minutes=ESPERAS_MINUTOS[entrega.tentativas - 1])
    entrega.save(
        update_fields=["status", "tentativas", "resposta_status", "ultimo_erro", "entregue_em", "proxima_tentativa"]
    )
    webhook.save(update_fields=["falhas_seguidas", "ultima_entrega_em"])
    return ok


def testar(webhook: WebhookSaida) -> EntregaWebhook:
    entrega = EntregaWebhook.objects.create(
        webhook=webhook,
        evento=EVENTO_TESTE,
        dados={"mensagem": "Teste de webhook do Gesttora"},
        proxima_tentativa=timezone.now(),
    )
    entregar(entrega)
    return entrega


def processar_fila(limite: int = 50) -> dict:
    agora = timezone.now()
    lote = list(
        EntregaWebhook.objects.select_related("webhook")
        .filter(status=EntregaWebhook.PENDENTE, proxima_tentativa__lte=agora, webhook__ativo=True)
        .order_by("proxima_tentativa")[:limite]
    )
    entregues = sum(entregar(e) for e in lote)
    EntregaWebhook.objects.filter(
        status__in=[EntregaWebhook.ENTREGUE, EntregaWebhook.DESISTIU], created_at__lt=agora - timedelta(days=30)
    ).delete()
    return {"processados": len(lote), "entregues": entregues, "falhas": len(lote) - entregues}
