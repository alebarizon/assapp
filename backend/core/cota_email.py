"""
Cota horária de envio de e-mail, compartilhada pelo backend e pelo agendador.

Envios em massa (fila da newsletter, réguas, lembretes de anuidade) consultam `cabe()`
e param quando a cota da última hora acaba; o restante sai nas execuções seguintes.
E-mails individuais (senha, convite, certificado) sempre saem e só descontam.
Quem registra é `core.email_backend.CotaSMTPBackend`. EMAIL_LIMITE_POR_HORA=0 desliga.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from core.models import EmailEnviado

logger = logging.getLogger(__name__)


def limite() -> int:
    return getattr(settings, "EMAIL_LIMITE_POR_HORA", 0)


def usados_na_ultima_hora() -> int:
    desde = timezone.now() - timedelta(hours=1)
    total = EmailEnviado.objects.filter(criado_em__gte=desde).aggregate(n=Sum("destinatarios"))["n"]
    return total or 0


def cabe(destinatarios: int = 1) -> bool:
    if not limite():
        return True
    return usados_na_ultima_hora() + destinatarios <= limite()


def registrar(destinatarios: int) -> None:
    if destinatarios <= 0:
        return
    try:
        with transaction.atomic():
            EmailEnviado.objects.create(destinatarios=destinatarios)
            EmailEnviado.objects.filter(criado_em__lt=timezone.now() - timedelta(days=2)).delete()
    except Exception:
        logger.exception("Falha ao registrar envio na cota de e-mail")
