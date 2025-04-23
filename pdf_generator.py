from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT

# Регистрация шрифтов
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))

def generate_import_pdf(breakdown, result, buffer, auction="—"):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(name='Normal', fontName='DejaVuSans', fontSize=10)
    bold = ParagraphStyle(name='Bold', fontName='DejaVuSans-Bold', fontSize=10, leading=12)
    bold_big = ParagraphStyle(name='BoldBig', fontName='DejaVuSans-Bold', fontSize=12, leading=14, alignment=TA_RIGHT, spaceBefore=10)

    elements = []

    # Логотип
    logo = Image("logo.png", width=200, height=100)
    elements.append(logo)
    elements.append(Spacer(1, 16))

    # Таблица
    table_data = [[Paragraph("<b>Параметр</b>", bold), Paragraph("<b>Значення</b>", bold)]]

    for k, v in breakdown.items():
        if k == "ПДВ":
            table_data.append([Paragraph("<b>Розмитнення авто</b>", bold), ""])
        val = f"${v:,.0f}" if isinstance(v, (int, float)) and "Год" not in k else v
        table_data.append([Paragraph(str(k), normal), Paragraph(str(val), normal)])

    # Итог жирным
    table_data.append([
        Paragraph("До сплати", bold_big),
        Paragraph(f"${result:,.0f}", bold_big)
    ])

    table = Table(table_data, colWidths=[110*mm, 60*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#38c4ef")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVuSans'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("SPAN", (0, len(table_data)-2), (1, len(table_data)-2)),
        ("BACKGROUND", (0, len(table_data)-2), (1, len(table_data)-2), colors.HexColor("#E6F7FF"))
    ]))

    elements.append(table)
    doc.build(elements)
