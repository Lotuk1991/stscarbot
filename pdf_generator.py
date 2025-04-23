from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

def generate_import_pdf(breakdown, result, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(name='Normal', fontName='DejaVu', fontSize=10)
    bold = ParagraphStyle(name='Bold', fontName='DejaVu', fontSize=10, leading=12, spaceAfter=6)

    elements = []

    # Логотип
    logo = Image("logo.png", width=200, height=100)
    elements.append(logo)
    elements.append(Spacer(1, 12))

    # Аукцион (в заголовок таблицы)
    auction = breakdown.get('Аукцион', '—')
    header_text = f"<b>Аукціон: {auction}</b>"
    elements.append(Paragraph(header_text, bold))
    elements.append(Spacer(1, 6))

    # Таблица
    table_data = [[Paragraph("<b>Параметр</b>", bold), Paragraph("<b>Значення</b>", bold)]]

    for k, v in breakdown.items():
        if k == 'Аукцион': continue  # Уже в заголовке
        val = f"${v:,.0f}" if isinstance(v, (int, float)) and "Год" not in k and "Рік" not in k else v
        table_data.append([
            Paragraph(str(k), normal),
            Paragraph(str(val), normal)
        ])

    # Итоговая строка
    table_data.append([
        Paragraph("<b>До сплати</b>", bold),
        Paragraph(f"<b>${result:,.0f}</b>", bold)
    ])

    table = Table(table_data, colWidths=[110 * mm, 60 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00B5F1")),  # Цвет логотипа
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)