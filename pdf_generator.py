from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Регистрация шрифта для поддержки кириллицы
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

def generate_import_pdf(breakdown, result, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = 'DejaVuSans'
    styles["Title"].fontName = 'DejaVuSans'
    elements = []

    # Логотип
    logo_path = "sts_logo.png"  # логотип должен быть в корне проекта
    if os.path.exists(logo_path):
        img = Image(logo_path, width=120, height=40)
        img.hAlign = 'CENTER'
        elements.append(img)

    elements.append(Spacer(1, 10))

    # Таблица расчёта
    table_data = [["<b>Параметр</b>", "<b>Значение</b>"]]

    # Блок растаможки
    customs_keys = [
        "Ввозная пошлина (10%)",
        "Акциз (EUR, пересчитан в USD)",
        "НДС (20%)",
        "Таможенные платежи (итого)"
    ]
    customs_block = []

    for k, v in breakdown.items():
        val = f"${v:,.0f}" if isinstance(v, (int, float)) and "Год" not in k else v
        if k in customs_keys:
            customs_block.append([k, val])
        else:
            table_data.append([k, val])

    # Вставляем блок растаможки
    table_data.append(["<b>Блок растаможки</b>", ""])
    table_data.extend(customs_block)

    # Итоговая сумма
    table_data.append(["<b>Итоговая сумма</b>", f"<b>${result:,.0f}</b>"])

    table = Table(table_data, colWidths=[110 * mm, 60 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
