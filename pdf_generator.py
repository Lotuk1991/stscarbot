from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Реєстрація шрифтів
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'DejaVuSans-Bold.ttf'))

def generate_import_pdf(breakdown, result, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()

    normal = ParagraphStyle(name='Normal', fontName='DejaVu', fontSize=10)
    bold = ParagraphStyle(name='Bold', fontName='DejaVu-Bold', fontSize=10)
    section_title = ParagraphStyle(name='SectionTitle', fontName='DejaVu-Bold', fontSize=10, textColor=colors.black)
    footer_style = ParagraphStyle(name='Footer', fontName='DejaVu', fontSize=9, alignment=1)

    header_color = colors.HexColor("#38c4ef")
    customs_keys = ['ПДВ (20%)', 'Ввізне мито (10%)', 'Акциз (EUR, перерахований в USD)', 'Митні платежі (всього)']
    additional_keys = ['Експедитор (Литва)', 'Брокерські послуги', 'Доставка в Україну', 'Сертифікація',
                       'Пенсійний фонд', 'МРЕВ (постановка на облік)', 'Послуги компанії']

    # Елементи PDF
    elements = []

    # Логотип
    elements.append(Image("logo.png", width=200, height=80))
    elements.append(Spacer(1, 16))

    # Формування таблиці
    data = [[Paragraph("Загальні витрати", section_title), ""]]
    general_rows = []
    customs_rows = []
    additional_rows = []

    for k, v in breakdown.items():
        if k in customs_keys or k in additional_keys:
            continue
        if k == 'Рік випуску':
            val = str(v)
        else:
            val = f"${v:,.0f}" if isinstance(v, (int, float)) else v
        general_rows.append([Paragraph(k, normal), Paragraph(val, normal)])

    data += general_rows

    customs_present = [k for k in customs_keys if k in breakdown]
    if customs_present:
        data.append([Paragraph("Митні платежі", section_title), ""])
        for k in customs_present:
            val = f"${breakdown[k]:,.0f}" if isinstance(breakdown[k], (int, float)) else breakdown[k]
            customs_rows.append([Paragraph(k, normal), Paragraph(val, normal)])
        data += customs_rows

    additional_present = [k for k in additional_keys if k in breakdown]
    if additional_present:
        data.append([Paragraph("Додаткові витрати", section_title), ""])
        for k in additional_present:
            val = f"${breakdown[k]:,.0f}" if isinstance(breakdown[k], (int, float)) else breakdown[k]
            additional_rows.append([Paragraph(k, normal), Paragraph(val, normal)])
        data += additional_rows

    # Підсумок
    data.append([
        Paragraph("<b>До сплати</b>", bold),
        Paragraph(f"<b>${result:,.0f}</b>", bold)
    ])

    # Побудова таблиці
    table = Table(data, colWidths=[110 * mm, 60 * mm])
    customs_start = 1 + len(general_rows)
    additional_start = customs_start + len(customs_rows) + (1 if customs_rows else 0)

    table.setStyle(TableStyle([
        # Заголовки секцій
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, customs_start), (-1, customs_start), header_color),
        ("TEXTCOLOR", (0, customs_start), (-1, customs_start), colors.black),
        ("BACKGROUND", (0, additional_start), (-1, additional_start), header_color),
        ("TEXTCOLOR", (0, additional_start), (-1, additional_start), colors.white),

        # Виділення рядка "Митні платежі (всього)"
        ("BACKGROUND", (0, customs_start + len(customs_rows)), (-1, customs_start + len(customs_rows)), colors.lightgrey),

        # Стилі таблиці
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # Футер з іконками
    contacts = (
        "<para alignment='center'>"
        "<img src='icons8-viber-48.png' width='10' height='10'/> "
        "<img src='icons8-whatsapp-48.png' width='10' height='10'/> "
        "<img src='icons8-telegram-48.png' width='10' height='10'/> "
        "<b>+380934853975</b> | м.Київ | "
        "<a href='https://stscars.com.ua'>stscars.com.ua</a> | "
        "<a href='https://www.instagram.com/sts_cars'>Instagram</a> | "
        "<a href='https://t.me/stscars'>Telegram</a>"
        "</para>"
    )
    elements.append(Paragraph(contacts, footer_style))

    doc.build(elements)