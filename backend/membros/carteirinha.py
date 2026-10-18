"""Carteirinha digital do associado: situação, validade, QR de verificação e PDF."""
from __future__ import annotations

import base64
import secrets
from datetime import date
from io import BytesIO
from urllib.parse import urlencode

from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from .models import Anuidade, AnuidadeStatus, FiliacaoStatus, Membro
from .services import membro_adimplente

SITUACAO_LABEL = {"em_dia": "Em dia", "pendente": "Anuidade pendente", "inativo": "Filiação inativa"}


def _novo_codigo() -> str:
    return secrets.token_urlsafe(12)


@transaction.atomic
def garantir_carteirinha(membro: Membro) -> Membro:
    """Atribui matrícula sequencial e código de QR na primeira emissão."""
    campos = []
    if membro.matricula is None:
        ultima = Membro.objects.select_for_update().aggregate(m=Max("matricula"))["m"] or 0
        membro.matricula = ultima + 1
        campos.append("matricula")
    if not membro.carteirinha_codigo:
        membro.carteirinha_codigo = _novo_codigo()
        campos.append("carteirinha_codigo")
    if campos:
        try:
            with transaction.atomic():
                membro.save(update_fields=campos + ["updated_at"])
        except IntegrityError:
            membro.refresh_from_db()
            return garantir_carteirinha(membro)
    return membro


def renovar_codigo(membro: Membro) -> Membro:
    """Novo QR (perda/vazamento da carteirinha): o código anterior deixa de validar."""
    garantir_carteirinha(membro)
    membro.carteirinha_codigo = _novo_codigo()
    membro.save(update_fields=["carteirinha_codigo", "updated_at"])
    return membro


def _filiacao_vigente(membro: Membro):
    return (
        membro.filiacoes.filter(status__in=[FiliacaoStatus.ATIVA, FiliacaoStatus.HONORARIA])
        .order_by("-data_inicio")
        .first()
        or membro.filiacoes.order_by("-data_inicio").first()
    )


def situacao(membro: Membro, hoje: date | None = None) -> dict:
    hoje = hoje or timezone.localdate()
    filiacao = _filiacao_vigente(membro)
    honoraria = bool(filiacao and filiacao.status == FiliacaoStatus.HONORARIA)

    if not membro.ativo or not filiacao or filiacao.status not in (FiliacaoStatus.ATIVA, FiliacaoStatus.HONORARIA):
        codigo = "inativo"
    elif membro_adimplente(membro):
        codigo = "em_dia"
    else:
        codigo = "pendente"

    valida_ate = None
    if codigo == "em_dia" and not honoraria:
        anuidades = list(
            Anuidade.objects.filter(filiacao__membro=membro).values_list("ano_referencia", "status", "vencimento")
        )
        quitadas = [ano for ano, st, _ in anuidades if st in (AnuidadeStatus.PAGA, AnuidadeStatus.ISENTA)]
        candidatos = [date(max(quitadas), 12, 31)] if quitadas else []
        candidatos += [
            venc for _, st, venc in anuidades
            if venc and st in (AnuidadeStatus.PENDENTE, AnuidadeStatus.VENCIDA) and venc >= hoje
        ]
        valida_ate = max(candidatos) if candidatos else None

    inicio = membro.filiacoes.order_by("data_inicio").values_list("data_inicio", flat=True).first()
    return {
        "situacao": codigo,
        "situacao_display": SITUACAO_LABEL[codigo],
        "valida_ate": valida_ate,
        "honoraria": honoraria,
        "tipo": filiacao.get_tipo_display() if filiacao else "",
        "membro_desde": inicio,
    }


def url_verificacao(schema: str, membro: Membro) -> str:
    from core.emails import frontend_url

    return frontend_url(f"/site/carteirinha/{membro.carteirinha_codigo}?{urlencode({'schema': schema})}")


def _qr_drawing(conteudo: str, tamanho: float):
    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.graphics.shapes import Drawing

    widget = QrCodeWidget(conteudo)
    x0, y0, x1, y1 = widget.getBounds()
    drawing = Drawing(tamanho, tamanho, transform=[tamanho / (x1 - x0), 0, 0, tamanho / (y1 - y0), 0, 0])
    drawing.add(widget)
    return drawing


def qr_svg_data_uri(conteudo: str) -> str:
    from reportlab.graphics import renderSVG

    svg = renderSVG.drawToString(_qr_drawing(conteudo, 160))
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def dados_carteirinha(membro: Membro, schema: str, associacao: str) -> dict:
    garantir_carteirinha(membro)
    url = url_verificacao(schema, membro)
    return {
        "nome": membro.nome_completo,
        "matricula": f"{membro.matricula:06d}",
        "instituicao": membro.instituicao or "",
        "associacao": associacao,
        "codigo": membro.carteirinha_codigo,
        "url_verificacao": url,
        "qr": qr_svg_data_uri(url),
        **situacao(membro),
    }


def build_carteirinha_pdf(membro: Membro, schema: str, associacao: str) -> bytes:
    """Cartão 85,6 × 54 mm (padrão ISO de cartão de crédito)."""
    from reportlab.graphics import renderPDF
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    dados = dados_carteirinha(membro, schema, associacao)
    largura, altura = 85.6 * mm, 54 * mm
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(largura, altura))
    pdf.setTitle(f"Carteirinha - {dados['nome']}")

    pdf.setFillColor(HexColor("#1a5f4a"))
    pdf.rect(0, altura - 12 * mm, largura, 12 * mm, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawString(4 * mm, altura - 6 * mm, associacao[:48])
    pdf.setFont("Helvetica", 6.5)
    pdf.drawString(4 * mm, altura - 9.5 * mm, "Carteira de associado")

    pdf.setFillColor(HexColor("#131313"))
    pdf.setFont("Helvetica-Bold", 9.5)
    nome = dados["nome"] if len(dados["nome"]) <= 34 else dados["nome"][:33] + "…"
    pdf.drawString(4 * mm, altura - 18 * mm, nome)

    cinza = HexColor("#4b5563")
    linhas = [
        ("Matrícula", dados["matricula"]),
        ("Categoria", dados["tipo"] or "—"),
        (
            "Validade",
            "Sócio honorário" if dados["honoraria"]
            else dados["valida_ate"].strftime("%d/%m/%Y") if dados["valida_ate"]
            else "—",
        ),
    ]
    if dados["membro_desde"]:
        linhas.append(("Associado desde", dados["membro_desde"].strftime("%m/%Y")))
    y = altura - 23.5 * mm
    for rotulo, valor in linhas:
        pdf.setFont("Helvetica", 5.5)
        pdf.setFillColor(cinza)
        pdf.drawString(4 * mm, y, rotulo.upper())
        pdf.setFont("Helvetica-Bold", 7.5)
        pdf.setFillColor(HexColor("#131313"))
        pdf.drawString(4 * mm, y - 3 * mm, valor[:34])
        y -= 7 * mm

    tamanho = 26 * mm
    renderPDF.draw(_qr_drawing(dados["url_verificacao"], tamanho), pdf, largura - tamanho - 3 * mm, 8 * mm)
    pdf.setFont("Helvetica", 5)
    pdf.setFillColor(cinza)
    pdf.drawCentredString(largura - tamanho / 2 - 3 * mm, 5 * mm, "Confira a situação atual")
    pdf.drawCentredString(largura - tamanho / 2 - 3 * mm, 3 * mm, "pelo QR code")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
