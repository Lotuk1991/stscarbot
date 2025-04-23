from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
import io

def generate_import_pdf(breakdown, result, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Логотип
    logo_path = "logo.png"  # путь к логотипу PNG без фона
    logo = Image(logo_path, width=140*mm, height=45*mm)
    elements.append(logo)
    elements.append(Spacer(1, 10))

    # Таблица
    table_data = []

    table_data.append(["1", "Ціна авто", f"${breakdown['Ціна авто']:,}"])
    table_data.append(["2", "Комісія аукціону", f"${breakdown['Комісія аукціону']:,}"])
    table_data.append(["3", "Доставка до Клайпеди", f"${breakdown['Доставка до Клайпеди']:,}"])

    # Блок 2 – Розмитнення
    table_data.append(["4", "Розмитнення авто", ""])
    table_data.append(["", "Рік випуску", breakdown["Рік випуску"]])
    table_data.append(["", "Паливо", breakdown["Паливо"]])
    table_data.append(["", "Об’єм двигуна", breakdown["Об’єм двигуна"]])
    table_data.append(["", "ПДВ", f"${breakdown['ПДВ']:,}"])
    table_data.append(["", "Ввізне мито", f"${breakdown['Ввізне мито']:,}"])
    table_data.append(["", "Акциз", f"${breakdown['Акциз']:,}"])
    table_data.append(["", "Сума розмитнення", f"${breakdown['Сума розмитнення']:,}"])

    table_data.append(["5", "Експедиція (Литва)", f"${breakdown['Експедиція (Литва)']:,}"])
    table_data.append(["6", "Брокер", f"${breakdown['Брокер']:,}"])
    table_data.append(["7", "Доставка по Україні", f"${breakdown['Доставка по Україні']:,}"])
    table_data.append(["8", "Сертифікація", f"${breakdown['Сертифікація']:,}"])
    table_data.append(["9", "Пенсійний фонд", f"${breakdown['Пенсійний фонд']:,}"])
    table_data.append(["10", "МРЕО", f"${breakdown['МРЕО']:,}"])
    table_data.append(["11", "Послуги компанії", f"${breakdown['Послуги компанії']:,}"])

    # Итог
    table_data.append(["", "До сплати", f"${result:,}"])

    table = Table(table_data, colWidths=[20*mm, 110*mm, 50*mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1.2, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (0, 3), (2, 3)),  # строка "Розмитнення авто"
    ]))

    elements.append(table)
    doc.build(elements)