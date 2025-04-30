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
    header = ParagraphStyle(name='Header', fontName='DejaVu-Bold', fontSize=12, textColor=colors.HexColor("#38c4ef"))
    footer = ParagraphStyle(name='Footer', fontName='DejaVu', fontSize=9, alignment=1)

    elements = []

    # Логотип
    elements.append(Image("logo.png", width=200, height=80))
    elements.append(Spacer(1, 16))

    # Цвет блока заголовков
    header_color = colors.HexColor("#38c4ef")

    # Блоки ключей
    customs_keys = ['ПДВ', 'Ввізне мито', 'Акциз', 'Митні платежі (всього)']
    additional_keys = [
        'Експедитор (Литва)', 'Брокерські послуги', 'Доставка в Україну',
        'Сертифікація', 'Пенсійний фонд', 'МРЕВ (постановка на облік)', 'Послуги компанії'
    ]

    # Общая таблица
    data = []

    # Вставка аукциона как первый элемент
    if auction:
        data.append([Paragraph("Аукціон", normal), Paragraph(auction.capitalize(), normal)])

    # Основные строки
    for k, v in breakdown.items():
        if k in customs_keys or k in additional_keys:
            continue
        val = f"${v:,.0f}" if isinstance(v, (int, float)) else v
        data.append([Paragraph(k, normal), Paragraph(str(val), normal)])

    # ===== Митні платежі =====
    customs_present = [k for k in customs_keys if k in breakdown]
    customs_section_start = len(data)
    if customs_present:
        data.append([Paragraph("Митні платежі", bold), ""])
        for k in customs_present:
            v = breakdown[k]
            val = f"${v:,.0f}" if isinstance(v, (int, float)) else v
            data.append([Paragraph(k, normal), Paragraph(str(val), normal)])

    # ===== Додаткові витрати =====
    additional_present = [k for k in additional_keys if k in breakdown]
    additional_section_start = len(data)
    if additional_present:
        data.append([Paragraph("Додаткові витрати", bold), ""])
        for k in additional_present:
            v = breakdown[k]
            val = f"${v:,.0f}" if isinstance(v, (int, float)) else v
            data.append([Paragraph(k, normal), Paragraph(str(val), normal)])

    # ===== Итог =====
    data.append([
        Paragraph("<b>До сплати</b>", bold),
        Paragraph(f"<b>${result:,.0f}</b>", bold)
    ])

    # ===== Таблица =====
    table = Table(data, colWidths=[110 * mm, 60 * mm])
    table.setStyle(TableStyle([
        # Заголовок таблицы
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        # Цвет "Митні платежі"
        ("BACKGROUND", (0, customs_section_start), (-1, customs_section_start), header_color),
        ("TEXTCOLOR", (0, customs_section_start), (-1, customs_section_start), colors.white),

        # Цвет "Додаткові витрати"
        ("BACKGROUND", (0, additional_section_start), (-1, additional_section_start), header_color),
        ("TEXTCOLOR", (0, additional_section_start), (-1, additional_section_start), colors.white),

        # Итог
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
        # Общие стили
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 14))

    # ===== Футер =====
    contacts = (
        "<img src='icons8-viber-48.png' width='12'/> "
        "<img src='icons8-whatsapp-48.png' width='12'/> "
        "<img src='icons8-telegram-48.png' width='12'/> "
        "<b>+380934853975</b> | м.Київ | "
        "<a href='https://stscars.com.ua'>stscars.com.ua</a> | "
        "<a href='https://www.instagram.com/sts_cars'>Instagram</a> | "
        "<a href='https://t.me/stscars'>Telegram</a>"
    )
    elements.append(Paragraph(contacts, footer))

    doc.build(elements)