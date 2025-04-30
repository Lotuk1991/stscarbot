from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'DejaVuSans-Bold.ttf'))

def generate_import_pdf(breakdown, result, buffer, auction=None):
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=40)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(name='Normal', fontName='DejaVu', fontSize=10)
    bold = ParagraphStyle(name='Bold', fontName='DejaVu-Bold', fontSize=10)
    header_style = ParagraphStyle(name='Header', fontName='DejaVu-Bold', fontSize=12, alignment=1)

    elements = []

    # Логотип
    logo = Image("logo.png", width=200, height=80)
    elements.append(logo)
    elements.append(Spacer(1, 10))

    header_color = colors.HexColor("#38c4ef")

    customs_keys = ['ПДВ', 'Ввізне мито', 'Акциз', 'Сума розмитнення']
    general_section, customs_section = [], []

    # Вставим аукцион перед Ціна авто
    if auction:
        general_section.append([
            Paragraph("Аукціон", normal),
            Paragraph(auction.capitalize(), normal)
        ])

    for k, v in breakdown.items():
        val = f"${v:,.0f}" if isinstance(v, (int, float)) else v
        row = [Paragraph(k, normal), Paragraph(val, normal)]
        if k in customs_keys:
            customs_section.append(row)
        else:
            general_section.append(row)

    data = []

    # Блок: Загальні витрати
    data.append([Paragraph("Загальні витрати", bold), ""])
    data += general_section

    # Блок: Розмитнення авто
    if customs_section:
        data.append([Paragraph("Розмитнення авто", bold), ""])
        data += customs_section

    # Итог
    data.append([
        Paragraph("До сплати", bold),
        Paragraph(f"<b>${result:,.0f}</b>", bold)
    ])

    table = Table(data, colWidths=[110 * mm, 60 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, len(general_section)+1), (-1, len(general_section)+1), header_color),
        ("TEXTCOLOR", (0, len(general_section)+1), (-1, len(general_section)+1), colors.white),
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 15))

    # Футер с контактами
    contact_data = [
        [
            Image("viber.png", width=10, height=10),
            Image("whatsapp.png", width=10, height=10),
            Image("telegram.png", width=10, height=10),
            Paragraph("+380934853975", normal)
        ],
        [
            "", "", "", Paragraph("м.Київ", normal)
        ],
        [
            "", "", "", Paragraph("stscars.com.ua", normal)
        ],
        [
            "", "", "", Paragraph("Instagram: https://www.instagram.com/sts_cars", normal)
        ],
        [
            "", "", "", Paragraph("Telegram: https://t.me/stscars", normal)
        ],
    ]

    contact_table = Table(contact_data, colWidths=[12*mm, 12*mm, 12*mm, 140*mm])
    elements.append(contact_table)

    doc.build(elements)