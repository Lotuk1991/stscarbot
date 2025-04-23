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
    bold.fontName = 'DejaVu'
    bold.fontSize = 10
    bold.leading = 12

    elements = []

    # Логотип (в 2 раза больше)
    try:
        logo = Image("logo.png", width=200, height=100)
        elements.append(logo)
        elements.append(Spacer(1, 10))
    except Exception as e:
        print(f"Ошибка с логотипом: {e}")

    # Таблица
    table_data = [[Paragraph("Параметр", bold), Paragraph("Значение", bold)]]
    for k, v in breakdown.items():
        val = f"${v:,.0f}" if isinstance(v, (int, float)) and "Год" not in k else v
        table_data.append([
            Paragraph(str(k), normal),
            Paragraph(str(val), normal)
        ])

    table_data.append([
        Paragraph("Итоговая сумма", bold),
        Paragraph(f"${result:,.0f}", bold)
    ])

    table = Table(table_data, colWidths=[110*mm, 60*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)