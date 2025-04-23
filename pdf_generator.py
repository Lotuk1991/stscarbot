from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Регистрируем шрифт с поддержкой кириллицы
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

def generate_import_pdf(breakdown, result, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    styles["Title"].fontName = 'DejaVu'
    styles["Normal"].fontName = 'DejaVu'

    elements = []

    # Добавляем логотип
    try:
        logo = Image("logo.png", width=100, height=50)  # Укажи путь и размеры логотипа
        elements.append(logo)
        elements.append(Spacer(1, 12))
    except Exception as e:
        print(f"Ошибка при добавлении логотипа: {e}")

    elements.append(Paragraph("🚗 <b>Финальный расчёт по импорту авто</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    table_data = [["<b>Параметр</b>", "<b>Значение</b>"]]
    for k, v in breakdown.items():
        val = f"${v:,.0f}" if isinstance(v, (int, float)) and "Год" not in k else v
        table_data.append([k, val])
    table_data.append(["<b>Итоговая сумма</b>", f"<b>${result:,.0f}</b>"])

    table = Table(table_data, colWidths=[110*mm, 60*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)