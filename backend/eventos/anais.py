"""Anais por trabalho: publicação, citação (ABNT, APA, BibTeX) e PDF."""
from __future__ import annotations

import unicodedata
from io import BytesIO
from urllib.parse import urlencode

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from .cientifico import nome_autor
from .models import (
    AnaisPublicacao,
    EventoAcademico,
    EventoAcademicoStatus,
    SubmissaoStatus,
    SubmissaoTrabalho,
    TrabalhoPublicado,
)

STATUS_PUBLICAVEIS = [SubmissaoStatus.ACEITO, SubmissaoStatus.ACEITO_COM_REVISOES]
SUFIXOS_NOME = {"junior", "júnior", "jr", "jr.", "filho", "neto", "sobrinho", "segundo", "terceiro"}
MESES = ["jan.", "fev.", "mar.", "abr.", "maio", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."]
LICENCA_URL = {
    "cc-by": "https://creativecommons.org/licenses/by/4.0/deed.pt_BR",
    "cc-by-sa": "https://creativecommons.org/licenses/by-sa/4.0/deed.pt_BR",
    "cc-by-nc": "https://creativecommons.org/licenses/by-nc/4.0/deed.pt_BR",
    "cc-by-nc-nd": "https://creativecommons.org/licenses/by-nc-nd/4.0/deed.pt_BR",
}


# ------------------------------------------------------------------ Publicação


def autores_da_submissao(s: SubmissaoTrabalho) -> list[dict]:
    principal = {"nome": nome_autor(s), "instituicao": "", "orcid": ""}
    if s.membro_id:
        principal["instituicao"] = s.membro.instituicao or ""
        principal["orcid"] = s.membro.orcid or ""
    coautores = [
        {"nome": c.get("nome", ""), "instituicao": c.get("instituicao", ""), "orcid": ""}
        for c in s.coautores or []
        if c.get("nome")
    ]
    return [principal] + coautores


def _slug_unico(anais: AnaisPublicacao, titulo: str, atual: TrabalhoPublicado | None = None) -> str:
    base = slugify(titulo)[:100].strip("-") or "trabalho"
    existentes = set(anais.trabalhos.exclude(pk=getattr(atual, "pk", None)).values_list("slug", flat=True))
    slug, n = base, 2
    while slug in existentes:
        slug = f"{base}-{n}"
        n += 1
    return slug


def _copiar_pdf(origem: SubmissaoTrabalho, destino: TrabalhoPublicado) -> None:
    if not origem.arquivo or not origem.arquivo.name.lower().endswith(".pdf"):
        return
    with origem.arquivo.open("rb") as f:
        destino.arquivo.save(f"{destino.slug}.pdf", ContentFile(f.read()), save=False)


@transaction.atomic
def publicar_anais(evento: EventoAcademico, titulo: str | None = None, issn: str | None = None) -> AnaisPublicacao:
    """Cria/atualiza os anais e sincroniza um `TrabalhoPublicado` por trabalho aceito.

    Republicar preserva slug, DOI e PDF final de quem já estava nos anais (os links citados não quebram).
    """
    cfp = getattr(evento, "call_for_papers", None)
    if not cfp:
        raise ValueError("Evento não possui Call for Papers.")

    anais = AnaisPublicacao.objects.filter(evento=evento).first() or AnaisPublicacao(evento=evento)
    if titulo or not anais.titulo:
        anais.titulo = titulo or f"Anais — {evento.titulo}"
    if issn is not None:
        anais.issn = issn or None
    if not anais.cidade and evento.local:
        anais.cidade = evento.local[:100]
    anais.publicado_em = anais.publicado_em or timezone.now()
    anais.save()

    aceitas = list(
        cfp.submissoes.filter(status__in=STATUS_PUBLICAVEIS)
        .select_related("autor", "membro")
        .order_by("area_tematica", "titulo")
    )
    anais.trabalhos.filter(submissao__isnull=False).exclude(submissao__in=aceitas).delete()

    for ordem, s in enumerate(aceitas, start=1):
        dados = {
            "titulo": s.titulo,
            "resumo": s.resumo,
            "palavras_chave": s.palavras_chave or [],
            "autores": autores_da_submissao(s),
            "area_tematica": s.area_tematica or "",
            "ordem": ordem,
        }
        trabalho = TrabalhoPublicado.objects.filter(submissao=s).first()
        if trabalho:
            for campo, valor in dados.items():
                setattr(trabalho, campo, valor)
        else:
            trabalho = TrabalhoPublicado(anais=anais, submissao=s, **dados)
            trabalho.slug = _slug_unico(anais, s.titulo)
            _copiar_pdf(s, trabalho)
        trabalho.save()

    trabalhos = list(anais.trabalhos.all())
    anais.metadata = {
        "total_trabalhos": len(trabalhos),
        "trabalhos": [
            {
                "id": str(t.submissao_id or t.id),
                "slug": t.slug,
                "titulo": t.titulo,
                "autor": ", ".join(a["nome"] for a in t.autores),
                "area_tematica": t.area_tematica,
                "palavras_chave": t.palavras_chave,
            }
            for t in trabalhos
        ],
        "gerado_automaticamente": True,
    }
    anais.save(update_fields=["metadata"])

    evento.status = EventoAcademicoStatus.ANAIS_PUBLICADOS
    evento.save(update_fields=["status", "updated_at"])
    return anais


def url_publica(schema: str, trabalho: TrabalhoPublicado) -> str:
    from core.emails import frontend_url

    evento = trabalho.anais.evento
    return frontend_url(f"/site/eventos/{evento.slug}/anais/{trabalho.slug}?{urlencode({'schema': schema})}")


# ------------------------------------------------------------------ Citação


def _partes_nome(nome: str) -> tuple[str, list[str]]:
    """(sobrenome, prenomes). Sufixos como Filho/Júnior acompanham o último sobrenome."""
    tokens = nome.split()
    if len(tokens) <= 1:
        return nome, []
    corte = -2 if tokens[-1].lower() in SUFIXOS_NOME and len(tokens) > 2 else -1
    return " ".join(tokens[corte:]), tokens[:corte]


def nome_abnt(nome: str) -> str:
    sobrenome, prenomes = _partes_nome(nome)
    return f"{sobrenome.upper()}, {' '.join(prenomes)}" if prenomes else sobrenome.upper()


def nome_apa(nome: str) -> str:
    sobrenome, prenomes = _partes_nome(nome)
    iniciais = " ".join(f"{p[0].upper()}." for p in prenomes if p[0].isalpha() and p.lower() not in {"da", "de", "do", "das", "dos", "e"})
    return f"{sobrenome}, {iniciais}" if iniciais else sobrenome


def _ascii(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def citacoes(trabalho: TrabalhoPublicado, associacao: str, url: str, hoje=None) -> dict:
    anais = trabalho.anais
    evento = anais.evento
    ano = (anais.publicado_em or trabalho.publicado_em).year
    nomes = [a["nome"] for a in trabalho.autores if a.get("nome")]
    doi_url = f"https://doi.org/{trabalho.doi}" if trabalho.doi else ""
    hoje = hoje or timezone.localdate()

    partes_abnt = [
        f"{'; '.join(nome_abnt(n) for n in nomes)}.",
        f"{trabalho.titulo.rstrip('.')}.",
        f"In: {evento.titulo.upper()}, {evento.data_inicio.year}" + (f", {evento.local}." if evento.local else "."),
        f"Anais [...]. {anais.cidade or '[S. l.]'}: {associacao or '[s. n.]'}, {ano}.",
    ]
    if anais.issn:
        partes_abnt.append(f"ISSN {anais.issn}.")
    if anais.isbn:
        partes_abnt.append(f"ISBN {anais.isbn}.")
    if trabalho.doi:
        partes_abnt.append(f"DOI: {trabalho.doi}.")
    partes_abnt.append(f"Disponível em: {url}. Acesso em: {hoje.day} {MESES[hoje.month - 1]} {hoje.year}.")

    autores_apa = [nome_apa(n) for n in nomes]
    if len(autores_apa) > 1:
        lista_apa = ", ".join(autores_apa[:-1]) + ", & " + autores_apa[-1]
    else:
        lista_apa = autores_apa[0] if autores_apa else associacao
    apa = f"{lista_apa} ({ano}). {trabalho.titulo.rstrip('.')}. In {anais.titulo}. {associacao}. {doi_url or url}"

    primeiro = _partes_nome(nomes[0])[0] if nomes else "anon"
    palavra = next((w for w in slugify(trabalho.titulo).split("-") if len(w) > 3), "trabalho")
    chave = f"{_ascii(primeiro).lower().replace(' ', '')}{ano}{palavra}"
    campos = [
        ("title", trabalho.titulo),
        ("author", " and ".join(f"{_partes_nome(n)[0]}, {' '.join(_partes_nome(n)[1])}".strip(", ") for n in nomes)),
        ("booktitle", anais.titulo),
        ("year", str(ano)),
        ("publisher", associacao),
        ("address", anais.cidade),
        ("issn", anais.issn or ""),
        ("isbn", anais.isbn),
        ("doi", trabalho.doi),
        ("url", url),
        ("keywords", ", ".join(trabalho.palavras_chave)),
    ]
    corpo = ",\n".join(f"  {k} = {{{v.replace('{', '').replace('}', '')}}}" for k, v in campos if v)
    bibtex = f"@inproceedings{{{chave},\n{corpo}\n}}"

    return {"abnt": " ".join(partes_abnt), "apa": apa, "bibtex": bibtex}


# ------------------------------------------------------------------ PDF


def build_trabalho_pdf(trabalho: TrabalhoPublicado, associacao: str, url: str) -> bytes:
    """PDF do trabalho quando não há arquivo final: folha de rosto com resumo e citação."""
    from xml.sax.saxutils import escape

    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    anais = trabalho.anais
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=2.5 * cm, rightMargin=2.5 * cm, topMargin=2.5 * cm, bottomMargin=2.5 * cm,
        title=trabalho.titulo, author=", ".join(a["nome"] for a in trabalho.autores), subject=anais.titulo,
    )
    base = getSampleStyleSheet()
    cinza = HexColor("#4b5563")
    estilos = {
        "cab": ParagraphStyle("cab", parent=base["Normal"], fontSize=9, textColor=cinza),
        "titulo": ParagraphStyle("titulo", parent=base["Title"], fontSize=17, leading=22, spaceAfter=10),
        "autores": ParagraphStyle("autores", parent=base["Normal"], fontSize=11, alignment=1, leading=15),
        "secao": ParagraphStyle("secao", parent=base["Heading4"], spaceBefore=14),
        "texto": ParagraphStyle("texto", parent=base["Normal"], fontSize=10.5, leading=15, alignment=4),
        "pe": ParagraphStyle("pe", parent=base["Normal"], fontSize=8.5, leading=12, textColor=cinza),
    }

    ids = " · ".join(filter(None, [f"ISSN {anais.issn}" if anais.issn else "", f"ISBN {anais.isbn}" if anais.isbn else ""]))
    autores = "<br/>".join(
        escape(a["nome"]) + (f" <font color='#4b5563'>({escape(a['instituicao'])})</font>" if a.get("instituicao") else "")
        for a in trabalho.autores
    )
    elementos = [
        Paragraph(escape(f"{anais.titulo} · {associacao}" + (f" · {ids}" if ids else "")), estilos["cab"]),
        Spacer(1, 18),
        Paragraph(escape(trabalho.titulo), estilos["titulo"]),
        Paragraph(autores, estilos["autores"]),
        Paragraph("Resumo", estilos["secao"]),
        Paragraph(escape(trabalho.resumo).replace("\n", "<br/>"), estilos["texto"]),
    ]
    if trabalho.palavras_chave:
        elementos.append(
            Paragraph(f"<b>Palavras-chave:</b> {escape('; '.join(trabalho.palavras_chave))}.", estilos["texto"])
        )
    if trabalho.area_tematica:
        elementos.append(Paragraph(f"<b>Área temática:</b> {escape(trabalho.area_tematica)}", estilos["texto"]))
    elementos += [
        Paragraph("Como citar", estilos["secao"]),
        Paragraph(escape(citacoes(trabalho, associacao, url)["abnt"]), estilos["texto"]),
        Spacer(1, 24),
        Paragraph(
            escape(f"{anais.get_licenca_display()} · {url}" + (f" · DOI {trabalho.doi}" if trabalho.doi else "")),
            estilos["pe"],
        ),
    ]
    doc.build(elementos)
    return buffer.getvalue()
