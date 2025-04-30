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
    normal = ParagraphStyle(name='Normal', fontName='DejaVu', fontSize=10)
    bold = ParagraphStyle(name='Bold', fontName='DejaVu-Bold', fontSize=10)
    section_header = ParagraphStyle(name='Header', fontName='DejaVu-Bold', fontSize=10, textColor=colors.white)
    footer = ParagraphStyle(name='Footer', fontName='DejaVu', fontSize=9)

    elements = []

    # Логотип
    logo = Image("logo.png", width=200, height=80)
    elements.append(logo)
    elements.append(Spacer(1, 16))

    header_color = colors.HexColor("#38c4ef")
    customs_keys = ['ПДВ', 'Ввізне мито', 'Акциз', 'Сума розмитнення']
    additional_keys = ['Експедитор (Литва)', 'Брокерські послуги', 'Доставка в Україну', 'Сертифікація', 'Пенсійний фонд', 'МРЕВ (постановка на облік)', 'Послуги компанії']

    data = []

    # ===== Загальні витрати =====
    data.append([Paragraph("Загальні витрати", section_header), ""])

    # Добавляем "Аукціон"
    if auction:
        data.append([Paragraph("Аукціон", normal), Paragraph(auction.capitalize(), normal)])

    customs_section = []
    for k in customs_keys:
        if k in breakdown:
            v = breakdown[k]
            val = f"${v:,.0f}" if isinstance(v, (int, float)) else v
            customs_section.append([Paragraph(k, normal), Paragraph(val, normal)])

    # Основные значения (все, кроме таможни и доп. расходов)
    for k, v in breakdown.items():
        if k in customs_keys or k in additional_keys or k == 'Аукціон':
            continue
        val = f"${v:,.0f}" if isinstance(v, (int, float)) else v
        data.append([Paragraph(k, normal), Paragraph(val, normal)])

    # Вставляем блок "Митні платежі"
    if customs_section:
        data.append([Paragraph("Митні платежі", section_header), ""])
        data += customs_section

    # ===== Додаткові витрати =====
    data.append([Paragraph("Додаткові витрати", section_header), ""])
    for k in additional_keys:
        if k in breakdown:
            v = breakdown[k]
            val = f"${v:,.0f}" if isinstance(v, (int, float)) else v
            data.append([Paragraph(k, normal), Paragraph(val, normal)])

    # ===== Итог =====
    data.append([
        Paragraph("<b>До сплати</b>", bold),
        Paragraph(f"<b>${result:,.0f}</b>", bold)
    ])

    table = Table(data, colWidths=[110 * mm, 60 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, len(data) - len(additional_keys) - 2), (-1, len(data) - len(additional_keys) - 2), header_color),
        ("TEXTCOLOR", (0, len(data) - len(additional_keys) - 2), (-1, len(data) - len(additional_keys) - 2), colors.white),
        ("BACKGROUND", (0, len(data) - 1), (-1, len(data) - 1), colors.lightgrey),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # ===== Футер =====
    contacts = (
        "<img src='icons8-viber-48.png' width='11' height='11' valign='middle'/> "
        "<img src='icons8-whatsapp-48.png' width='11' height='11' valign='middle'/> "
        "<img src='icons8-telegram-48.png' width='11' height='11' valign='middle'/> "
        "<b>+380934853975</b> | м.Київ | "
        "<a href='https://stscars.com.ua'>stscars.com.ua</a> | "
        "<a href='https://www.instagram.com/sts_cars'>Instagram</a> | "
        "<a href='https://t.me/stscars'>Telegram</a>"
    )
    elements.append(Paragraph(contacts, footer))

    doc.build(elements)