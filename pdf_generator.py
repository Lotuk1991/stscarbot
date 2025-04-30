def generate_import_pdf(breakdown, result, buffer, auction=None):
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(name='Normal', fontName='DejaVu', fontSize=10)
    bold = ParagraphStyle(name='Bold', fontName='DejaVu-Bold', fontSize=10)
    center_bold = ParagraphStyle(name='CenterBold', fontName='DejaVu-Bold', fontSize=12, alignment=1)  # центр
    section_title = ParagraphStyle(name='SectionTitle', fontName='DejaVu-Bold', fontSize=10, textColor=colors.white)

    elements = []

    # Логотип
    logo = Image("logo.png", width=200, height=80)
    elements.append(logo)
    elements.append(Spacer(1, 18))

    # Название аукциона — по центру, черным
    if auction:
        elements.append(Paragraph(f"Аукціон: {auction.capitalize()}", center_bold))
        elements.append(Spacer(1, 14))

    # Цвет блока заголовков
    header_color = colors.HexColor("#38c4ef")

    # Разделение на два блока
    customs_keys = ['ПДВ', 'Ввізне мито', 'Акциз', 'Сума розмитнення']
    customs_section = []
    general_section = []

    for k, v in breakdown.items():
        val = f"${v:,.0f}" if isinstance(v, (int, float)) else v
        row = [Paragraph(str(k), normal), Paragraph(str(val), normal)]
        if k in customs_keys:
            customs_section.append(row)
        else:
            general_section.append(row)

    # Формируем таблицу
    data = []

    # Блок: Загальні витрати
    data.append([Paragraph("Загальні витрати", section_title), ""])
    data += general_section

    # Блок: Розмитнення авто
    if customs_section:
        data.append([Paragraph("Розмитнення авто", section_title), ""])
        data += customs_section

    # Итог
    data.append([
        Paragraph("<b>До сплати</b>", bold),
        Paragraph(f"<b>${result:,.0f}</b>", bold)
    ])

    table = Table(data, colWidths=[110 * mm, 60 * mm])
    table.setStyle(TableStyle([
        # Шапки блоков
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, len(general_section)+1), (-1, len(general_section)+1), header_color),
        ("TEXTCOLOR", (0, len(general_section)+1), (-1, len(general_section)+1), colors.white),
        # Итог
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
        # Остальные стили
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), 'DejaVu'),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    doc.build(elements)