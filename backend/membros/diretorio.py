"""
Diretório público de associados.

Aparece quem deu opt-in no portal e tem filiação ativa ou honorária. Expõe só dados
acadêmicos que o próprio associado escolheu publicar — nunca e-mail, telefone ou CPF.
"""
from collections import Counter

from django.db.models import Q

from .models import FiliacaoStatus, Membro

POR_PAGINA = 24


def membros_no_diretorio():
    return (
        Membro.objects.filter(
            ativo=True,
            diretorio_publico=True,
            filiacoes__status__in=[FiliacaoStatus.ATIVA, FiliacaoStatus.HONORARIA],
        )
        .distinct()
        .prefetch_related("filiacoes")
        .order_by("nome_completo")
    )


def _cartao(membro: Membro) -> dict:
    filiacoes = sorted(membro.filiacoes.all(), key=lambda f: f.data_inicio)
    vigente = next(
        (f for f in reversed(filiacoes) if f.status in (FiliacaoStatus.ATIVA, FiliacaoStatus.HONORARIA)), None
    )
    return {
        "id": str(membro.id),
        "nome": membro.nome_completo,
        "instituicao": membro.instituicao or "",
        "area_atuacao": membro.area_atuacao or "",
        "mini_bio": membro.mini_bio,
        "lattes_url": membro.lattes_url or "",
        "orcid": membro.orcid or "",
        "categoria": vigente.get_tipo_display() if vigente else "",
        "membro_desde": filiacoes[0].data_inicio.year if filiacoes else None,
    }


def buscar(q: str = "", instituicao: str = "", pagina: int = 1) -> dict:
    base = membros_no_diretorio()
    instituicoes = Counter(
        (i or "").strip() for i in base.values_list("instituicao", flat=True) if (i or "").strip()
    )
    qs = base
    if q:
        qs = qs.filter(
            Q(nome_completo__icontains=q) | Q(instituicao__icontains=q)
            | Q(area_atuacao__icontains=q) | Q(mini_bio__icontains=q)
        )
    if instituicao:
        qs = qs.filter(instituicao__iexact=instituicao)
    total = qs.count()
    pagina = max(pagina, 1)
    inicio = (pagina - 1) * POR_PAGINA
    return {
        "total": total,
        "pagina": pagina,
        "paginas": max((total + POR_PAGINA - 1) // POR_PAGINA, 1),
        "resultados": [_cartao(m) for m in qs[inicio:inicio + POR_PAGINA]],
        "instituicoes": [{"nome": n, "total": c} for n, c in sorted(instituicoes.items(), key=lambda x: (-x[1], x[0]))[:40]],
    }
