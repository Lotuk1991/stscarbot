from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Регистрация шрифта
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

def generate_import_pdf(breakdown, result, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='NormalCyr', parent=styles['Normal'], fontName='DejaVuSans'))
    styles.add(ParagraphStyle(name='BoldCyr', parent=styles['Heading4'], fontName='DejaVuSans'))
    normal = styles['NormalCyr']
    bold = styles['BoldCyr']
    elements = []

    # Логотип
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        img = Image(logo_path, width=140, height=50)
        elements.append(img)
        elements.append(Spacer(1, 8))

    # Таблица данных в структуре как в оригинале
    rows = []

    rows.append(["1", Paragraph("Цiна авто", normal), f"${breakdown.get('Цена авто', 0):,.0f}"])
    rows.append(["2", Paragraph("Комiсiя аукцiону", normal), f"${breakdown.get('Сбор аукциона', 0):,.0f}"])
    rows.append(["3", Paragraph("Доставка до Клайпеди", normal), f"${breakdown.get('Доставка в Клайпеду', 0):,.0f}"])

    rows.append(["4", Paragraph("Розмитнення авто", bold), ""])
    rows.append(["", Paragraph("Рік випуску", normal), str(breakdown.get('Год выпуска', ''))])
    rows.append(["", Paragraph("Паливо", normal), str(breakdown.get('Тип топлива', ''))])
    rows.append(["", Paragraph("Обʼєм двигуна", normal), str(breakdown.get('Объем двигателя', ''))])
    rows.append(["", Paragraph("ПДВ", normal), f"${breakdown.get('НДС (20%)', 0):,.0f}"])
    rows.append(["", Paragraph("Ввізне мито", normal), f"${breakdown.get('Ввозная пошлина (10%)', 0):,.0f}"])
    rows.append(["", Paragraph("Акциз", normal), f"${breakdown.get('Акциз (EUR, пересчитан в USD)', 0):,.0f}"])
    rows.append(["", Paragraph("Сума розмитнення", bold), f"${breakdown.get('Таможенные платежи (итого)', 0):,.0f}"])

    rows.append(["5", Paragraph("Експедиція (Литва)", normal), f"${breakdown.get('Экспедитор (Литва)', 0):,.0f}"])
    rows.append(["6", Paragraph("Брокер", normal), f"${breakdown.get('Брокерские услуги', 0):,.0f}"])
    rows.append(["7", Paragraph("Доставка по Україні", normal), f"${breakdown.get('Доставка в Украину', 0):,.0f}"])
    rows.append(["8", Paragraph("Сертифікація", normal), f"${breakdown.get('Сертификация', 0):,.0f}"])
    rows.append(["9", Paragraph("Пенсійний фонд", normal), f"${breakdown.get('Пенсионный фонд (3%)', 0):,.0f}"])
    rows.append(["10", Paragraph("МРЕО", normal), f"${breakdown.get('МРЭО (постановка на учет)', 0):,.0f}"])
    rows.append(["11", Paragraph("Послуги компанії", normal), f"${breakdown.get('Услуги компании', 0):,.0f}"])

    rows.append(["", Paragraph("<b>До сплати</b>", bold), Paragraph(f"<b>${result:,.0f}</b>", bold)])

    table = Table(rows, colWidths=[15*mm, 120*mm, 45*mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVuSans'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4)
    ]))

    elements.append(table)
    doc.build(elements)
