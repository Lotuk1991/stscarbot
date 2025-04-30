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
    header_style = ParagraphStyle(name='Header', fontName='DejaVu-Bold', fontSize=12, alignment=1)
    footer_style = ParagraphStyle(name='Footer', fontName='DejaVu', fontSize=9, alignment=1)

    elements = []

    # Логотип
    logo = Image("logo.png", width=200, height=80)
    elements.append(logo)
    elements.append(Spacer(1, 16))

    # Цвет заголовков секций
    header_color = colors.HexColor("#38c4ef")

    # Ключи блоков
    customs_keys = ['ПДВ (20%)', 'Ввізне мито (10%)', 'Акциз (EUR, перерахований в USD)', 'Митні платежі (всього)']
    additional_keys = ['Експедитор (Литва)', 'Брокерські послуги', 'Доставка в Україну', 'Сертифікація', 'Пенсійний фонд', 'МРЕВ (постановка на облік)', 'Послуги компанії']

    # Сборка таблицы
    data = [[Paragraph("Загальні витрати", bold), ""]]

    # Основной блок
    for k, v in breakdown.items():
    if k not in customs_keys and k not in additional_keys:
        if k == "Рік випуску":
            val = f"{v}"  # без доллара
        elif isinstance(v, (int, float)):
            val = f"${v:,.0f}"
        else:
            val = v
        data.append([Paragraph(k, normal), Paragraph(val, normal)])
        if k == 'Рік випуску':
            # После года добавляем блок "Митні платежі"
            customs_present = [key for key in customs_keys if key in breakdown]
            if customs_present:
                data.append([Paragraph("Митні платежі", bold), ""])
                for ck in customs_present:
                    val = f"${breakdown[ck]:,.0f}" if isinstance(breakdown[ck], (int, float)) else breakdown[ck]
                    row_style = ("BACKGROUND", (0, len(data)), (-1, len(data)), colors.lightgrey) if ck == 'Митні платежі (всього)' else None
                    data.append([Paragraph(ck, normal), Paragraph(val, normal)])
                    if row_style:
                        # позже добавим стиль на эту строку
                        pass

    # Блок дополнительных
    additional_present = [key for key in additional_keys if key in breakdown]
    if additional_present:
        data.append([Paragraph("Додаткові витрати", bold), ""])
        for ak in additional_present:
            val = f"${breakdown[ak]:,.0f}" if isinstance(breakdown[ak], (int, float)) else breakdown[ak]
            data.append([Paragraph(ak, normal), Paragraph(val, normal)])

    # Итог
    data.append([
        Paragraph("<b>До сплати</b>", bold),
        Paragraph(f"<b>${result:,.0f}</b>", bold)
    ])

    # Таблица и стили
    table = Table(data, colWidths=[110 * mm, 60 * mm])
    customs_title_index = next((i for i, row in enumerate(data) if row[0].getPlainText() == "Митні платежі"), None)
    customs_total_index = next((i for i, row in enumerate(data) if "Митні платежі (всього)" in row[0].getPlainText()), None)
    additional_index = next((i for i, row in enumerate(data) if row[0].getPlainText() == "Додаткові витрати"), None)

    style = [
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
    ]

    if customs_title_index:
        style.append(("BACKGROUND", (0, customs_title_index), (-1, customs_title_index), header_color))
        style.append(("TEXTCOLOR", (0, customs_title_index), (-1, customs_title_index), colors.black))

    if customs_total_index:
        style.append(("BACKGROUND", (0, customs_total_index), (-1, customs_total_index), colors.lightgrey))

    if additional_index:
        style.append(("BACKGROUND", (0, additional_index), (-1, additional_index), header_color))
        style.append(("TEXTCOLOR", (0, additional_index), (-1, additional_index), colors.black))

    table.setStyle(TableStyle(style))
    elements.append(table)
    elements.append(Spacer(1, 16))

    # Футер
    contacts = (
        "<img src='icons8-viber-48.png' width='10' height='10'/> "
        "<img src='icons8-whatsapp-48.png' width='10' height='10'/> "
        "<img src='icons8-telegram-48.png' width='10' height='10'/> "
        "<b>+380934853975</b> | м.Київ | "
        "<a href='https://stscars.com.ua'>stscars.com.ua</a> | "
        "<a href='https://www.instagram.com/sts_cars'>Instagram</a> | "
        "<a href='https://t.me/stscars'>Telegram</a>"
    )
    elements.append(Paragraph(contacts, footer_style))
    doc.build(elements)