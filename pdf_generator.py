from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Шрифты
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'DejaVuSans-Bold.ttf'))

def generate_import_pdf(breakdown, result, buffer, auction=None):
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(name='Normal', fontName='DejaVu', fontSize=10)
    bold = ParagraphStyle(name='Bold', fontName='DejaVu-Bold', fontSize=10)
    section_title = ParagraphStyle(name='SectionTitle', fontName='DejaVu-Bold', fontSize=10, textColor=colors.black)
    footer_style = ParagraphStyle(name='Footer', fontName='DejaVu', fontSize=8, alignment=1)

    elements = []

    # Логотип
    logo = Image("logo.png", width=200, height=80)
    elements.append(logo)
    elements.append(Spacer(1, 14))

    # Ключевые блоки
    customs_keys = ['ПДВ (20%)', 'Ввізне мито (10%)', 'Акциз (EUR, перерахований в USD)', 'Митні платежі (всього)']
    additional_keys = ['Експедитор (Литва)', 'Брокерські послуги', 'Доставка в Україну', 'Сертифікація', 'Пенсійний фонд', 'МРЕВ (постановка на облік)', 'Послуги компанії']

    data = [[Paragraph("Загальні витрати", section_title), ""]]

    if auction:
        data.append([Paragraph("Аукціон", normal), Paragraph(auction.capitalize(), normal)])

    general_keys = [k for k in breakdown if k not in customs_keys + additional_keys]
    for k in general_keys:
        val = f"${breakdown[k]:,.0f}" if isinstance(breakdown[k], (int, float)) else breakdown[k]
        data.append([Paragraph(k, normal), Paragraph(val, normal)])

    # Митні платежі
    customs_present = [k for k in customs_keys if k in breakdown]
    if customs_present:
        data.append([Paragraph("Митні платежі", section_title), ""])
        for k in customs_present:
            val = f"${breakdown[k]:,.0f}" if isinstance(breakdown[k], (int, float)) else breakdown[k]
            data.append([Paragraph(k, normal), Paragraph(val, normal)])

    # Додаткові витрати
    additional_present = [k for k in additional_keys if k in breakdown]
    if additional_present:
        data.append([Paragraph("Додаткові витрати", section_title), ""])
        for k in additional_present:
            val = f"${breakdown[k]:,.0f}" if isinstance(breakdown[k], (int, float)) else breakdown[k]
            data.append([Paragraph(k, normal), Paragraph(val, normal)])

    # Итог
    data.append([
        Paragraph("<b>До сплати</b>", bold),
        Paragraph(f"<b>${result:,.0f}</b>", bold)
    ])

    table = Table(data, colWidths=[110 * mm, 60 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#38c4ef")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),

        ("BACKGROUND", (0, len(general_keys) + 1), (-1, len(general_keys) + 1), colors.HexColor("#38c4ef")),
        ("TEXTCOLOR", (0, len(general_keys) + 1), (-1, len(general_keys) + 1), colors.black),

        ("BACKGROUND", (0, len(data) - len(additional_present) - 2), (-1, len(data) - len(additional_present) - 2), colors.HexColor("#38c4ef")),
        ("TEXTCOLOR", (0, len(data) - len(additional_present) - 2), (-1, len(data) - len(additional_present) - 2), colors.black),

        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # Футер
    contacts = (
        "<para alignment='center'>"
        "<img src='icons8-viber-48.png' width='12' height='12'/> "
        "<img src='icons8-whatsapp-48.png' width='12' height='12'/> "
        "<img src='icons8-telegram-48.png' width='12' height='12'/> "
        "<b>+380934853975</b> | м.Київ | "
        "<a href='https://stscars.com.ua'>stscars.com.ua</a> | "
        "<a href='https://www.instagram.com/sts_cars'>Instagram</a> | "
        "<a href='https://t.me/stscars'>Telegram</a>"
        "</para>"
    )

    elements.append(Paragraph(contacts, footer_style))

    doc.build(elements)