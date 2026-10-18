"""Ficha 360 do contato: tudo o que a associação sabe da pessoa, pelo associado vinculado e pelo e-mail."""
from __future__ import annotations

from decimal import Decimal

from django.db.models import Sum

from membros.timeline import _quando, timeline_membro

from .models import Contato


def _item(quando, categoria: str, titulo: str, detalhe: str = "", link: str = "") -> dict | None:
    momento = _quando(quando)
    if not momento:
        return None
    return {"quando": momento, "categoria": categoria, "titulo": titulo, "detalhe": detalhe, "link": link}


def _por_email(email: str) -> list[dict | None]:
    """Atividade de quem ainda não é associado, achada pelo e-mail."""
    from eventos.models import InscricaoEvento, SubmissaoTrabalho
    from formularios.models import Resposta

    itens = []
    for inscricao in InscricaoEvento.objects.filter(email__iexact=email).select_related("evento"):
        itens.append(_item(inscricao.created_at, "evento", f"Inscrição em {inscricao.evento.titulo}"))
        if inscricao.certificado_emitido_em:
            itens.append(
                _item(inscricao.certificado_emitido_em, "evento", f"Certificado emitido — {inscricao.evento.titulo}")
            )
    for submissao in SubmissaoTrabalho.objects.filter(autor__email__iexact=email, submetido_em__isnull=False):
        itens.append(_item(submissao.submetido_em, "evento", "Trabalho submetido", submissao.titulo))
    for resposta in Resposta.objects.filter(email__iexact=email, enviada_em__isnull=False).select_related("formulario"):
        itens.append(_item(resposta.enviada_em, "formulario", "Formulário respondido", resposta.formulario.titulo))
    return itens


def ficha_contato(contato: Contato, limite: int = 200) -> dict:
    from eventos.models import InscricaoEvento, SubmissaoTrabalho
    from membros.carteirinha import situacao
    from membros.models import Membro

    email = contato.email.strip()
    membro = contato.membro
    outros = Contato.objects.filter(email__iexact=email).exclude(pk=contato.pk) if email else Contato.objects.none()

    itens = [
        _item(
            c.created_at,
            "contato",
            "Contato pelo site" if c.origem != Contato.MANUAL else "Contato cadastrado",
            c.get_assunto_display(),
            "" if c.pk == contato.pk else f"/app/contatos/{c.id}",
        )
        for c in [contato, *outros]
    ]

    if membro:
        itens += [i for i in timeline_membro(membro, limite=limite) if i["categoria"] != "contato"]
    elif email:
        itens += _por_email(email)

    itens = sorted((i for i in itens if i), key=lambda i: i["quando"], reverse=True)[:limite]

    associado = None
    sugerido = None
    if membro:
        associado = {"id": str(membro.id), "nome": membro.nome_completo, **situacao(membro)}
        pagos = membro.orders.filter(paid_at__isnull=False)
        total_pago = pagos.aggregate(t=Sum("total_amount"))["t"] or Decimal("0")
        resumo_pedidos = {"pedidos_pagos": pagos.count(), "total_pago": f"{total_pago:.2f}"}
        eventos = membro.inscricoes_evento.count()
        trabalhos = membro.submissoes.exclude(submetido_em__isnull=True).count()
    else:
        resumo_pedidos = {"pedidos_pagos": 0, "total_pago": "0.00"}
        eventos = InscricaoEvento.objects.filter(email__iexact=email).count() if email else 0
        trabalhos = (
            SubmissaoTrabalho.objects.filter(autor__email__iexact=email, submetido_em__isnull=False).count()
            if email
            else 0
        )
        mesmo_email = Membro.objects.filter(email__iexact=email).first() if email else None
        if mesmo_email:
            sugerido = {"id": str(mesmo_email.id), "nome": mesmo_email.nome_completo}

    return {
        "resumo": {
            "associado": associado,
            "associado_mesmo_email": sugerido,
            "contatos": 1 + outros.count(),
            "eventos": eventos,
            "trabalhos": trabalhos,
            **resumo_pedidos,
            "ultima_atividade": itens[0]["quando"] if itens else None,
        },
        "itens": itens,
    }
