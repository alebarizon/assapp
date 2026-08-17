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


def _categoria_pedido_item(item_type: str) -> str:
    from ecommerce.models import CatalogItemType

    if item_type == CatalogItemType.ANUIDADE:
        return IncomeCategory.ANUIDADE
    if item_type == CatalogItemType.INSCRICAO:
        return IncomeCategory.EVENTO
    return IncomeCategory.OUTROS


def espelhar_pagamento_pedido(order, user=None) -> list[Transaction]:
    """
    Espelha itens do pedido pago no finance (idempotente por order_item).
    Anuidades já espelhadas via registrar_pagamento são ignoradas aqui.
    """
    from ecommerce.models import CatalogItemType, OrderItem

    created: list[Transaction] = []
    mandato = None
    try:
        from mandatos.models import Mandato

        mandato = Mandato.get_ativo()
    except Exception:
        pass

    occurred = order.paid_at or timezone.now()
    membro_nome = order.membro.nome_completo if order.membro else "Cliente"

    for item in order.items.all():
        if item.item_type == CatalogItemType.ANUIDADE:
            continue
        ref = f"pedido_item:{item.id}"
        if Transaction.objects.filter(referencia=ref).exists():
            continue
        category = _categoria_pedido_item(item.item_type)
        nome = item.catalog_item.name if item.catalog_item_id else "Item"
        tx = Transaction.objects.create(
            user=user,
            mandato=mandato,
            description=f"Pedido {order.order_number} — {nome} ({membro_nome})",
            amount=item.subtotal,
            type=TransactionType.INCOME,
            category=category,
            occurred_at=occurred,
            referencia=ref,
        )
        created.append(tx)
    return created
