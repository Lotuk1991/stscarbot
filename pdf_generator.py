from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Регистрация шрифта с поддержкой кириллицы
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

def generate_import_pdf(breakdown, result, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='NormalCyr', parent=styles['Normal'], fontName='DejaVu'))
    styles.add(ParagraphStyle(name='BoldCyr', parent=styles['Heading4'], fontName='DejaVu'))

    elements = []

    # Логотип
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        img = Image(logo_path, width=200, height=100)
        elements.append(img)
        elements.append(Spacer(1, 12))

    # Заголовок
    elements.append(Paragraph("Финальный расчёт по импорту авто", styles['Title']))
    elements.append(Spacer(1, 12))

    # Таблица с таможенными платежами
    table_data = [
        [Paragraph("<b>Параметр</b>", styles['NormalCyr']), Paragraph("<b>Значение</b>", styles['NormalCyr'])],
        [Paragraph("Ввозная пошлина (10%)", styles['NormalCyr']), Paragraph(f"${breakdown['Ввозная пошлина (10%)']:.2f}", styles['NormalCyr'])],
        [Paragraph("Акциз (EUR, пересчитан в USD)", styles['NormalCyr']), Paragraph(f"${breakdown['Акциз (EUR, пересчитан в USD)']:.2f}", styles['NormalCyr'])],
        [Paragraph("НДС (20%)", styles['NormalCyr']), Paragraph(f"${breakdown['НДС (20%)']:.2f}", styles['NormalCyr'])],
        [Paragraph("<b>Таможенные платежи (итого)</b>", styles['NormalCyr']), Paragraph(f"<b>${breakdown['Таможенные платежи (итого)']:.2f}</b>", styles['NormalCyr'])]
    ]

    table = Table(table_data, colWidths=[110*mm, 60*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BOX", (0, 1), (-1, 4), 1, colors.red)  # Обводка блока с таможенными платежами
    ]))

    elements.append(table)
    doc.build(elements)