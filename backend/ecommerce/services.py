"""
Serviços e-commerce — checkout, pagamento e fulfillment por tipo de item.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from eventos.models import EventoAcademico, InscricaoEvento
from membros.models import Anuidade, AnuidadeStatus, Membro
from membros.services import get_valor_anuidade, registrar_pagamento, resolver_membro_do_user

from .models import (
    Cart,
    CartItem,
    CatalogItem,
    CatalogItemType,
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
)


def get_or_create_cart(membro: Membro) -> Cart:
    cart, _ = Cart.objects.get_or_create(membro=membro)
    return cart


def validate_cart_item_for_membro(catalog_item: CatalogItem, membro: Membro, quantity: int):
    """Regras de negócio antes de adicionar ao carrinho."""
    if not catalog_item.is_active:
        raise ValidationError("Item indisponível.")

    if catalog_item.item_type == CatalogItemType.ANUIDADE:
        filiacao = membro.filiacao_ativa
        if not filiacao:
            raise ValidationError("Associado sem filiação ativa para anuidade.")
        if catalog_item.tipo_filiacao and filiacao.tipo != catalog_item.tipo_filiacao:
            raise ValidationError("Este item de anuidade não corresponde ao seu tipo de filiação.")
        ano = catalog_item.anuidade_ano
        if Anuidade.objects.filter(
            filiacao=filiacao,
            ano_referencia=ano,
            status__in=[AnuidadeStatus.PAGA, AnuidadeStatus.ISENTA],
        ).exists():
            raise ValidationError(f"Anuidade {ano} já está quitada ou isenta.")
        if quantity != 1:
            raise ValidationError("Anuidade: quantidade máxima 1.")

    if catalog_item.item_type == CatalogItemType.INSCRICAO:
        evento = catalog_item.evento
        if not evento:
            raise ValidationError("Evento não configurado.")
        if InscricaoEvento.objects.filter(evento=evento, membro=membro, confirmada=True).exists():
            raise ValidationError("Você já possui inscrição confirmada neste evento.")
        if evento.capacidade_max is not None:
            inscritos = evento.inscricoes.filter(confirmada=True).count()
            if inscritos >= evento.capacidade_max:
                raise ValidationError("Evento esgotado.")
        if quantity != 1:
            raise ValidationError("Inscrição: quantidade máxima 1.")

    if catalog_item.inventory_count is not None and catalog_item.inventory_count < quantity:
        raise ValidationError(
            f"Estoque insuficiente. Disponível: {catalog_item.inventory_count}."
        )


@transaction.atomic
def create_order_from_cart(
    membro: Membro,
    *,
    payment_method: str = PaymentMethod.SIMULATED,
    notes: str = "",
    auto_pay: bool = True,
    user=None,
) -> Order:
    """Checkout: Order a partir do carrinho; opcionalmente paga e cumpre na hora (MVP)."""
    try:
        cart = Cart.objects.select_for_update().get(membro=membro)
    except Cart.DoesNotExist:
        raise ValidationError("Carrinho vazio.")

    cart_items = list(
        cart.items.select_related("catalog_item", "catalog_item__evento").all()
    )
    if not cart_items:
        raise ValidationError("Carrinho vazio.")

    for ci in cart_items:
        validate_cart_item_for_membro(ci.catalog_item, membro, ci.quantity)

    total = Decimal("0")
    order = Order.objects.create(
        membro=membro,
        total_amount=Decimal("0"),
        currency="BRL",
        status=OrderStatus.PENDING,
        notes=notes or "",
    )

    line_items: list[OrderItem] = []
    for ci in cart_items:
        subtotal = ci.catalog_item.price * ci.quantity
        total += subtotal
        line_items.append(
            OrderItem(
                order=order,
                catalog_item=ci.catalog_item,
                item_type=ci.catalog_item.item_type,
                quantity=ci.quantity,
                price_at_purchase=ci.catalog_item.price,
                subtotal=subtotal,
            )
        )

    OrderItem.objects.bulk_create(line_items)
    order.total_amount = total
    order.save(update_fields=["total_amount"])

    cart.items.all().delete()

    if auto_pay:
        process_order_payment(order, payment_method=payment_method, user=user)

    order.refresh_from_db()
    return order


@transaction.atomic
def process_order_payment(
    order: Order,
    *,
    payment_method: str = PaymentMethod.MANUAL,
    user=None,
) -> Order:
    """Marca pedido pago, reduz estoque e executa fulfillment."""
    if order.status in (OrderStatus.PAID, OrderStatus.FULFILLED):
        return order
    if order.status == OrderStatus.CANCELLED:
        raise ValidationError("Pedido cancelado.")

    order.status = OrderStatus.PAID
    order.payment_method = payment_method
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "payment_method", "paid_at", "updated_at"])

    items = list(order.items.select_related("catalog_item", "catalog_item__evento"))
    for item in items:
        catalog = item.catalog_item
        if catalog.inventory_count is not None:
            if catalog.inventory_count < item.quantity:
                raise ValidationError(f"Estoque insuficiente: {catalog.name}")
            catalog.inventory_count -= item.quantity
            catalog.save(update_fields=["inventory_count", "updated_at"])

        ref = fulfill_order_item(order, item, user=user)
        if ref:
            item.fulfillment_ref = ref
            item.save(update_fields=["fulfillment_ref"])

    try:
        from finance.services import espelhar_pagamento_pedido

        espelhar_pagamento_pedido(order, user=user)
    except Exception:
        pass

    order.status = OrderStatus.FULFILLED
    order.save(update_fields=["status", "updated_at"])
    return order


def fulfill_order_item(order: Order, item: OrderItem, user=None) -> dict | None:
    """Efeito de domínio por tipo de item."""
    membro = order.membro
    if not membro:
        return None

    catalog = item.catalog_item

    if item.item_type == CatalogItemType.ANUIDADE:
        return _fulfill_anuidade(membro, catalog, user=user)

    if item.item_type == CatalogItemType.INSCRICAO:
        return _fulfill_inscricao(membro, catalog, user=user)

    # curso, material, digital — registro no pedido; entrega manual/futura
    return {"type": item.item_type, "catalog_item_id": str(catalog.id)}


def _fulfill_anuidade(membro: Membro, catalog: CatalogItem, user=None) -> dict:
    filiacao = membro.filiacao_ativa
    if not filiacao:
        raise ValidationError("Sem filiação ativa.")

    ano = catalog.anuidade_ano
    anuidade = Anuidade.objects.filter(filiacao=filiacao, ano_referencia=ano).first()
    if not anuidade:
        valor = catalog.price if catalog.price > 0 else get_valor_anuidade(filiacao.tipo)
        anuidade = Anuidade.objects.create(
            filiacao=filiacao,
            ano_referencia=ano,
            valor=valor,
            vencimento=timezone.now().date(),
            status=AnuidadeStatus.PENDENTE,
        )

    if anuidade.status not in (AnuidadeStatus.PAGA, AnuidadeStatus.ISENTA):
        registrar_pagamento(anuidade, user=user)

    return {"type": "anuidade", "id": str(anuidade.id), "ano": ano}


def _fulfill_inscricao(membro: Membro, catalog: CatalogItem, user=None) -> dict:
    evento: EventoAcademico = catalog.evento
    inscricao, created = InscricaoEvento.objects.get_or_create(
        evento=evento,
        membro=membro,
        defaults={
            "nome": membro.nome_completo,
            "email": membro.email,
            "confirmada": True,
            "pago_em": timezone.now(),
        },
    )
    if not created:
        inscricao.confirmada = True
        inscricao.pago_em = timezone.now()
        inscricao.save(update_fields=["confirmada", "pago_em"])

    return {"type": "inscricao", "id": str(inscricao.id), "evento_id": str(evento.id)}


def resolve_membro_for_ecommerce(user) -> Membro | None:
    return resolver_membro_do_user(user, auto_link=True)
