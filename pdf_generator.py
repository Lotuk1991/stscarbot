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

def generate_import_pdf(breakdown, result, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)

    styles = getSampleStyleSheet()
    normal = ParagraphStyle(name='Normal', fontName='DejaVu', fontSize=10)
    bold = ParagraphStyle(name='Bold', fontName='DejaVu-Bold', fontSize=10)
    block_title = ParagraphStyle(name='BlockTitle', fontName='DejaVu-Bold', fontSize=10, textColor=colors.black)
    gray_background = colors.lightgrey

    elements = []

    # Логотип
    logo = Image("logo.png", width=200, height=80)
    elements.append(logo)
    elements.append(Spacer(1, 16))

    # Ключи
    customs_keys = ['ПДВ (20%)', 'Ввізне мито (10%)', 'Акциз (EUR, перерахований в USD)', 'Митні платежі (всього)']
    additional_keys = [
        'Експедитор (Литва)', 'Брокерські послуги', 'Доставка в Україну',
        'Сертифікація', 'Пенсійний фонд', 'МРЕВ (постановка на облік)', 'Послуги компанії'
    ]

    # === Общие данные ===
    data = [[Paragraph("Загальні витрати", block_title), ""]]

    for k, v in breakdown.items():
        if k in customs_keys or k in additional_keys:
            continue
        val = f"${v:,.0f}" if isinstance(v, (int, float)) else v
        data.append([Paragraph(k, normal), Paragraph(str(val), normal)])

        if k == 'Рік випуску':
            data.append([Paragraph("Митні платежі", block_title), ""])
            # Вставим митні платежі
            for ck in customs_keys:
                if ck in breakdown:
                    val = f"${breakdown[ck]:,.0f}" if isinstance(breakdown[ck], (int, float)) else breakdown[ck]
                    style = gray_background if ck == 'Митні платежі (всього)' else None
                    row = [Paragraph(ck, normal), Paragraph(str(val), normal)]
                    data.append(row)
                    if style:
                        row_idx = len(data) - 1
                        # Добавим серую строку в стиле позже

    # === Дополнительные расходы ===
    data.append([Paragraph("Додаткові витрати", block_title), ""])
    for k in additional_keys:
        if k in breakdown:
            val = f"${breakdown[k]:,.0f}" if isinstance(breakdown[k], (int, float)) else breakdown[k]
            data.append([Paragraph(k, normal), Paragraph(str(val), normal)])

    # === ИТОГО ===
    data.append([
        Paragraph("<b>До сплати</b>", bold),
        Paragraph(f"<b>${result:,.0f}</b>", bold)
    ])

    # Таблица
    table = Table(data, colWidths=[110 * mm, 60 * mm])
    customs_start = None
    customs_end = None
    for i, row in enumerate(data):
        if row[0].getPlainText() == 'Митні платежі':
            customs_start = i + 1
        if customs_start and customs_end is None and row[0].getPlainText() == 'Митні платежі (всього)':
            customs_end = i

    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#38c4ef")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]

    # Цвет блоков
    for i, row in enumerate(data):
        if row[0].getPlainText() in ["Митні платежі", "Додаткові витрати"]:
            table_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#38c4ef")))
            table_style.append(("TEXTCOLOR", (0, i), (-1, i), colors.black))
        elif row[0].getPlainText() == "Митні платежі (всього)":
            table_style.append(("BACKGROUND", (0, i), (-1, i), colors.lightgrey))

    table.setStyle(TableStyle(table_style))

    elements.append(table)
    elements.append(Spacer(1, 14))

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
    elements.append(Paragraph(contacts, ParagraphStyle(name='Footer', fontName='DejaVu', fontSize=9)))

    doc.build(elements)