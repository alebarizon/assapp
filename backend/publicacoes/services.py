"""Regras de acesso (paywall) e vínculo com a loja."""
from __future__ import annotations

from decimal import Decimal

from django.utils import timezone

from accounts.access import nivel_acesso
from ecommerce.models import CatalogItem, CatalogItemType, OrderItem
from membros.models import Membro
from membros.services import membro_adimplente

from .models import AcessoPublicacao, Publicacao

MOTIVOS = {
    "publico": "Acesso aberto",
    "equipe": "Equipe da associação",
    "adimplente": "Incluída na sua anuidade",
    "comprado": "Comprada",
    "requer_adimplencia": "Exclusiva para associados em dia",
    "requer_compra": "Disponível na loja",
}


def comprou(membro: Membro | None, pub: Publicacao) -> bool:
    if not membro or not pub.catalog_item_id:
        return False
    return OrderItem.objects.filter(
        catalog_item_id=pub.catalog_item_id, order__membro=membro, order__paid_at__isnull=False
    ).exists()


def acesso(pub: Publicacao, user=None, membro: Membro | None = None) -> dict:
    """Se a pessoa pode baixar o arquivo e por quê."""
    if pub.acesso == AcessoPublicacao.PUBLICO:
        motivo = "publico"
    elif user is not None and nivel_acesso(user, "publicacoes"):
        motivo = "equipe"
    elif comprou(membro, pub):
        motivo = "comprado"
    elif pub.acesso == AcessoPublicacao.ASSOCIADOS and membro_adimplente(membro):
        motivo = "adimplente"
    elif pub.acesso == AcessoPublicacao.ASSOCIADOS:
        motivo = "requer_adimplencia"
    else:
        motivo = "requer_compra"
    liberado = motivo in ("publico", "equipe", "comprado", "adimplente")
    return {"liberado": liberado, "motivo": motivo, "motivo_display": MOTIVOS[motivo]}


def sincronizar_item_loja(pub: Publicacao, preco: Decimal | None, preco_socio: Decimal | None, user=None) -> None:
    """Cria/atualiza o item digital da loja; sem preço ou acesso aberto, o item sai da vitrine."""
    item = pub.catalog_item
    vende = preco is not None and pub.acesso != AcessoPublicacao.PUBLICO
    if not vende:
        if item and item.is_active:
            item.is_active = False
            item.save(update_fields=["is_active", "updated_at"])
        return
    if item is None:
        item = CatalogItem(item_type=CatalogItemType.DIGITAL, created_by=user)
    item.name = pub.titulo[:200]
    item.description = pub.resumo
    item.price = preco
    item.member_price = preco_socio
    item.is_active = pub.publicada
    item.metadata = {**(item.metadata or {}), "publicacao": str(pub.id)}
    item.full_clean(exclude=["slug"])
    item.save()
    if pub.catalog_item_id != item.id:
        pub.catalog_item = item
        pub.save(update_fields=["catalog_item", "updated_at"])


def publicar(pub: Publicacao, publicada: bool) -> None:
    if publicada and not pub.publicado_em:
        pub.publicado_em = timezone.now()
    pub.publicada = publicada
    pub.save(update_fields=["publicada", "publicado_em", "updated_at"])
    item = pub.catalog_item
    if item:
        ativo = publicada and pub.acesso != AcessoPublicacao.PUBLICO
        if item.is_active != ativo:
            item.is_active = ativo
            item.save(update_fields=["is_active", "updated_at"])
