from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Шрифт с кириллицей
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

def generate_import_pdf(breakdown, result, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(name='Normal', fontName='DejaVu', fontSize=10)
    bold = ParagraphStyle(name='Bold', fontName='DejaVu', fontSize=10, leading=12, spaceAfter=6)

    elements = []

    # Логотип (в 2 раза больше)
    logo = Image("logo.png", width=200, height=100)
    elements.append(logo)
    elements.append(Spacer(1, 10))

    # Заголовок таблицы — аукцион
    auction_name = breakdown.get("Аукцион", "Аукцион")
    table_data = [[Paragraph(f"<b>Аукцион: {auction_name}</b>", bold), ""]]

    # Составление таблицы
    for k, v in breakdown.items():
        if k == "Аукцион":
            continue
        val = f"${v:,.0f}" if isinstance(v, (int, float)) and "Год" not in k else v
        table_data.append([Paragraph(k, normal), Paragraph(val, normal)])

    # Итоговая сумма
    table_data.append([
        Paragraph("<b>До сплати</b>", bold),
        Paragraph(f"<b>${result:,.0f}</b>", bold)
    ])

    # Создание таблицы
    table = Table(table_data, colWidths=[110*mm, 60*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00B5F1")),  # Цвет заголовка как в логотипе
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)