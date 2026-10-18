"""Serviços de pagamento online — cobrança de anuidade e de pedidos da loja, confirmação via webhook."""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ecommerce.models import Order, OrderStatus, PaymentMethod
from membros.models import Anuidade, AnuidadeStatus
from membros.services import registrar_pagamento

from .gateways import AsaasGateway, GatewayError, SimuladoGateway
from .models import Cobranca, ConfiguracaoPagamento

logger = logging.getLogger(__name__)

EVENTOS_PAGO = {"PAYMENT_RECEIVED", "PAYMENT_CONFIRMED", "PAYMENT_RECEIVED_IN_CASH"}
EVENTOS_CANCELADO = {"PAYMENT_DELETED", "PAYMENT_REFUNDED"}
PRAZO_PEDIDO_DIAS = 3


def gateway_ativo(config: ConfiguracaoPagamento | None = None):
    """Gateway real se configurado; simulado só quando PAGAMENTO_SIMULADO está ligado."""
    config = config or ConfiguracaoPagamento.atual()
    if config.ativo and config.api_key:
        return AsaasGateway(config.api_key, sandbox=config.sandbox)
    if getattr(settings, "PAGAMENTO_SIMULADO", False):
        return SimuladoGateway()
    return None


def disponibilidade() -> dict:
    config = ConfiguracaoPagamento.atual()
    gateway = gateway_ativo(config)
    demo = bool(getattr(settings, "PAGAMENTO_SIMULADO", False))
    if gateway is None:
        return {"habilitado": False, "simulado": False, "metodos": [], "demo": demo}
    simulado = isinstance(gateway, SimuladoGateway)
    metodos = [Cobranca.PIX, Cobranca.CARTAO, Cobranca.BOLETO] if simulado else config.metodos_aceitos
    return {"habilitado": True, "simulado": simulado, "metodos": metodos, "demo": demo}


def _gateway_para(metodo: str):
    gateway = gateway_ativo()
    if gateway is None:
        raise ValidationError("Pagamento online não está habilitado. Fale com a secretaria.")
    if metodo not in disponibilidade()["metodos"]:
        raise ValidationError("Forma de pagamento não aceita pela associação.")
    return gateway


def _emitir(gateway, metodo: str, *, membro, descricao: str, valor, vencimento, **alvo) -> Cobranca:
    """Reaproveita a cobrança em aberto (mesmo alvo, método, provedor e valor) ou cria uma nova no gateway."""
    existente = Cobranca.objects.filter(
        metodo=metodo, provedor=gateway.provedor, status=Cobranca.PENDENTE, valor=valor, **alvo
    ).first()
    if existente:
        return existente

    cobranca = Cobranca.objects.create(
        membro=membro,
        descricao=descricao,
        valor=valor,
        metodo=metodo,
        provedor=gateway.provedor,
        vencimento=vencimento,
        **alvo,
    )
    try:
        resultado = gateway.criar_cobranca(cobranca, membro)
    except GatewayError as exc:
        cobranca.status = Cobranca.FALHOU
        cobranca.erro = str(exc)
        cobranca.save(update_fields=["status", "erro", "updated_at"])
        raise ValidationError(str(exc)) from exc

    cobranca.external_id = resultado.external_id
    cobranca.url_pagamento = resultado.url_pagamento
    cobranca.pix_copia_cola = resultado.pix_copia_cola
    cobranca.pix_qrcode_base64 = resultado.pix_qrcode_base64
    cobranca.payload = resultado.payload
    cobranca.save()
    return cobranca


def cobrar_anuidade(anuidade: Anuidade, metodo: str) -> Cobranca:
    """Gera (ou reaproveita) a cobrança em aberto da anuidade no método escolhido."""
    if anuidade.status not in (AnuidadeStatus.PENDENTE, AnuidadeStatus.VENCIDA):
        raise ValidationError("Esta anuidade não está em aberto.")
    if anuidade.valor <= 0:
        raise ValidationError("Anuidade sem valor a pagar.")
    gateway = _gateway_para(metodo)
    return _emitir(
        gateway,
        metodo,
        membro=anuidade.filiacao.membro,
        descricao=f"Anuidade {anuidade.ano_referencia}",
        valor=anuidade.valor,
        vencimento=anuidade.vencimento,
        anuidade=anuidade,
    )


def cobrar_pedido(pedido: Order, metodo: str) -> Cobranca:
    """Cobrança online de um pedido pendente da loja."""
    if pedido.status != OrderStatus.PENDING:
        raise ValidationError("Este pedido não está aguardando pagamento.")
    if pedido.total_amount <= 0:
        raise ValidationError("Pedido sem valor a pagar.")
    if not pedido.membro_id:
        raise ValidationError("Pedido sem associado vinculado.")
    gateway = _gateway_para(metodo)
    return _emitir(
        gateway,
        metodo,
        membro=pedido.membro,
        descricao=f"Pedido {pedido.order_number}",
        valor=pedido.total_amount,
        vencimento=timezone.localdate() + timedelta(days=PRAZO_PEDIDO_DIAS),
        pedido=pedido,
    )


def _cancelar_outras(cobranca: Cobranca, **alvo) -> None:
    outras = Cobranca.objects.filter(status=Cobranca.PENDENTE, **alvo).exclude(pk=cobranca.pk)
    gateway = gateway_ativo()
    for outra in outras:
        if gateway and outra.provedor == gateway.provedor and outra.external_id:
            try:
                gateway.cancelar_cobranca(outra.external_id)
            except GatewayError:
                logger.warning("Não foi possível cancelar a cobrança %s no gateway", outra.external_id)
        outra.status = Cobranca.CANCELADA
        outra.save(update_fields=["status", "updated_at"])


@transaction.atomic
def confirmar_cobranca(cobranca: Cobranca, pago_em=None, payload: dict | None = None) -> Cobranca:
    """Marca paga, quita o alvo (anuidade ou pedido, com espelho no financeiro) e cancela as outras tentativas."""
    cobranca = Cobranca.objects.select_for_update().get(pk=cobranca.pk)
    if cobranca.status == Cobranca.PAGA:
        return cobranca

    cobranca.status = Cobranca.PAGA
    cobranca.pago_em = pago_em or timezone.now()
    if payload:
        cobranca.payload = payload
    cobranca.save(update_fields=["status", "pago_em", "payload", "updated_at"])

    if cobranca.anuidade_id:
        anuidade = cobranca.anuidade
        if not anuidade.stripe_payment_id:
            anuidade.stripe_payment_id = cobranca.external_id
            anuidade.save(update_fields=["stripe_payment_id"])
        registrar_pagamento(anuidade)
        _cancelar_outras(cobranca, anuidade=anuidade)

    if cobranca.pedido_id:
        _quitar_pedido(cobranca)
        _cancelar_outras(cobranca, pedido_id=cobranca.pedido_id)

    return cobranca


def _quitar_pedido(cobranca: Cobranca) -> None:
    """O dinheiro já entrou: falha no fulfillment (ex.: estoque) fica registrada para a secretaria, sem desfazer o pago."""
    from ecommerce.services import process_order_payment

    pedido = cobranca.pedido
    if not pedido.stripe_payment_intent_id:
        pedido.stripe_payment_intent_id = cobranca.external_id
        pedido.save(update_fields=["stripe_payment_intent_id", "updated_at"])
    try:
        with transaction.atomic():
            process_order_payment(pedido, payment_method=PaymentMethod.ONLINE)
    except ValidationError as exc:
        logger.error("Pedido %s pago online mas não concluído: %s", pedido.order_number, exc)
        Order.objects.filter(pk=pedido.pk).update(
            notes=((pedido.notes or "") + f"\nPago online ({cobranca.external_id}), mas não concluído: "
                   f"{'; '.join(exc.messages)}").strip()
        )


def processar_webhook_asaas(payload: dict) -> str:
    """Aplica um evento do Asaas. Retorna o que foi feito (para log/resposta)."""
    evento = payload.get("event") or ""
    pagamento = payload.get("payment") or {}
    external_id = pagamento.get("id") or ""
    if not external_id:
        return "ignorado"

    cobranca = Cobranca.objects.filter(provedor=ConfiguracaoPagamento.ASAAS, external_id=external_id).first()
    if cobranca is None and pagamento.get("externalReference"):
        try:
            cobranca = Cobranca.objects.filter(pk=pagamento["externalReference"]).first()
        except (ValueError, ValidationError):
            cobranca = None
    if cobranca is None:
        return "desconhecido"

    if evento in EVENTOS_PAGO:
        confirmar_cobranca(cobranca, payload=payload)
        return "pago"
    if evento in EVENTOS_CANCELADO and cobranca.status == Cobranca.PENDENTE:
        cobranca.status = Cobranca.CANCELADA
        cobranca.payload = payload
        cobranca.save(update_fields=["status", "payload", "updated_at"])
        return "cancelado"
    return "ignorado"
