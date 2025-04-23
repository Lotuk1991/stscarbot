from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Шрифт с кириллицей
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

def generate_import_pdf(breakdown, result, buffer, auction="—"):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(name='Normal', fontName='DejaVu', fontSize=10)
    bold = ParagraphStyle(name='Bold', fontName='DejaVu', fontSize=10, leading=12)
    bold_big = ParagraphStyle(name='BoldBig', fontName='DejaVu', fontSize=11, leading=14)

    elements = []

    # Логотип
    logo = Image("logo.png", width=200, height=100)
    elements.append(logo)
    elements.append(Spacer(1, 16))  # увеличенный отступ

    # Аукцион как заголовок таблицы
    table_data = [[Paragraph(f"<b>Аукцион: {auction.upper()}</b>", bold), ""]]

    # Таблица
    for k, v in breakdown.items():
        val = f"${v:,.0f}" if isinstance(v, (int, float)) and "Год" not in k else v
        table_data.append([Paragraph(str(k), normal), Paragraph(str(val), normal)])

    # Итог жирным
    table_data.append([
        Paragraph("<b>До сплати</b>", bold_big),
        Paragraph(f"<b>${result:,.0f}</b>", bold_big)
    ])

    table = Table(table_data, colWidths=[110*mm, 60*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#38c4ef")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
