"""Serviços financeiros — espelho de anuidades, etc."""
from django.utils import timezone

from .models import IncomeCategory, Transaction, TransactionType


def espelhar_pagamento_anuidade(anuidade, user=None) -> Transaction | None:
    """
    Cria Transaction income categoria anuidade de forma idempotente.
    referencia = anuidade:<uuid>
    """
    ref = f"anuidade:{anuidade.id}"
    existing = Transaction.objects.filter(referencia=ref).first()
    if existing:
        return existing

    membro_nome = ""
    try:
        membro_nome = anuidade.filiacao.membro.nome_completo
    except Exception:
        membro_nome = "Associado"

    mandato = None
    try:
        from mandatos.models import Mandato

        mandato = Mandato.get_ativo()
    except Exception:
        pass

    occurred = anuidade.pago_em or timezone.now()
    return Transaction.objects.create(
        user=user,
        mandato=mandato,
        description=f"Anuidade {anuidade.ano_referencia} — {membro_nome}",
        amount=anuidade.valor,
        type=TransactionType.INCOME,
        category=IncomeCategory.ANUIDADE,
        occurred_at=occurred,
        referencia=ref,
    )
