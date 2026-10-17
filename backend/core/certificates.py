"""
Certificado em PDF (A4 paisagem) — cursos e eventos.
"""
from datetime import datetime
from io import BytesIO
from urllib.parse import urlencode


def certificate_verify_url(schema: str, code: str) -> str:
    from core.emails import frontend_url

    return frontend_url(f"/site/certificados?{urlencode({'schema': schema, 'codigo': code})}")


def build_certificate_pdf(
    *,
    participant_name: str,
    title: str,
    intro: str = "Certificamos que",
    action: str = "concluiu com aproveitamento o curso",
    details: str = "",
    issued_at: datetime,
    code: str,
    issuer: str,
    verify_url: str = "",
) -> bytes:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    width, height = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=(width, height))
    pdf.setTitle(f"Certificado - {title}")

    pdf.setStrokeColor(HexColor("#9a6a0b"))
    pdf.setLineWidth(6)
    pdf.rect(30, 30, width - 60, height - 60)
    pdf.setLineWidth(1)
    pdf.rect(42, 42, width - 84, height - 84)

    pdf.setFillColor(HexColor("#131313"))
    pdf.setFont("Helvetica-Bold", 34)
    pdf.drawCentredString(width / 2, height - 140, "Certificado")

    pdf.setFont("Helvetica", 16)
    pdf.setFillColor(HexColor("#4b5563"))
    pdf.drawCentredString(width / 2, height - 200, intro)

    pdf.setFont("Helvetica-Bold", 28)
    pdf.setFillColor(HexColor("#131313"))
    pdf.drawCentredString(width / 2, height - 250, participant_name[:70])

    pdf.setFont("Helvetica", 16)
    pdf.setFillColor(HexColor("#4b5563"))
    pdf.drawCentredString(width / 2, height - 295, action)

    pdf.setFont("Helvetica-Bold", 22)
    pdf.setFillColor(HexColor("#7a5208"))
    pdf.drawCentredString(width / 2, height - 335, title[:80])

    if details:
        pdf.setFont("Helvetica", 14)
        pdf.setFillColor(HexColor("#4b5563"))
        pdf.drawCentredString(width / 2, height - 370, details[:110])

    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(HexColor("#4b5563"))
    pdf.drawString(80, 90, f"Data: {issued_at.strftime('%d/%m/%Y')}")
    pdf.drawCentredString(width / 2, 90, issuer[:80])

    if verify_url:
        from reportlab.graphics import renderPDF
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics.shapes import Drawing

        size = 78
        widget = QrCodeWidget(verify_url)
        x0, y0, x1, y1 = widget.getBounds()
        drawing = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
        drawing.add(widget)
        renderPDF.draw(drawing, pdf, width - 80 - size, 104)
        pdf.drawRightString(width - 80, 90, f"Código: {code}")
        pdf.setFont("Helvetica", 8)
        pdf.drawRightString(width - 80, 76, "Verifique a autenticidade pelo QR code")
    else:
        pdf.drawRightString(width - 80, 90, f"Código: {code}")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
