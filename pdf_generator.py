from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Регистрация шрифтов
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'DejaVuSans-Bold.ttf'))

def generate_import_pdf(breakdown, result, buffer, auction=None):
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(name='Normal', fontName='DejaVu', fontSize=10, spaceAfter=5)
    bold = ParagraphStyle(name='Bold', fontName='DejaVu-Bold', fontSize=10, spaceAfter=5)
    header = ParagraphStyle(name='Header', fontName='DejaVu-Bold', fontSize=12, textColor=colors.HexColor("#38c4ef"), spaceAfter=10)

    elements = []

    # Логотип
    logo = Image("logo.png", width=200, height=80)
    elements.append(logo)
    elements.append(Spacer(1, 20))

    # Название аукциона
    if auction:
        elements.append(Paragraph(f"Аукціон: <b>{auction.capitalize()}</b>", header))
        elements.append(Spacer(1, 10))

    # Цвет заголовков блоков
    section_header_color = colors.HexColor("#38c4ef")

    # Разделение на два блока
    customs_keys = ['ПДВ', 'Ввізне мито', 'Акциз', 'Сума розмитнення']
    customs_section = []
    general_section = []

    for k, v in breakdown.items():
        val = f"${v:,.0f}" if isinstance(v, (int, float)) else v
        row = [Paragraph(str(k), normal), Paragraph(str(val), normal)]
        if k in customs_keys:
            customs_section.append(row)
        else:
            general_section.append(row)

    # ===== Основной блок =====
    data = [[Paragraph("Загальні витрати", bold), ""]]
    data += general_section

    # ===== Блок Розмитнення =====
    if customs_section:
        data.append([Paragraph("Розмитнення авто", bold), ""])
        data += customs_section

    # ===== Итог =====
    data.append([
        Paragraph("<b>До сплати</b>", bold),
        Paragraph(f"<b>${result:,.0f}</b>", bold)
    ])

    table = Table(data, colWidths=[110*mm, 60*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), section_header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, len(general_section) + 1), (-1, len(general_section) + 1), section_header_color),
        ("TEXTCOLOR", (0, len(general_section) + 1), (-1, len(general_section) + 1), colors.white),
        ("BACKGROUND", (-2, -1), (-1, -1), colors.lightgrey),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    doc.build(elements)