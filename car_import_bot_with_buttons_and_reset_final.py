# Импорт необходимых библиотек
import os
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from collections import defaultdict
from pdf_generator import generate_import_pdf
import tempfile
import io
from collections import defaultdict, deque
# Логирование
logging.basicConfig(level=logging.INFO)

# Токен бота из переменной окружения
API_TOKEN = '7772557710:AAE9YdvAK3rOr_BEFyV4grUx5l2nf8KybBs'  # временно открытый токен

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хранилище пользовательских данных
user_data = defaultdict(dict)
user_reports = defaultdict(list)
user_reports = defaultdict(lambda: deque(maxlen=5))

# Загрузка данных
with open('delivery_dict.json', 'r') as f:
    delivery_dict = json.load(f)
with open('copart_fee_data.json', 'r') as f:
    copart_fee_data = json.load(f)
with open('iaai_fee_data.json', 'r') as f:
    iaai_fee_data = json.load(f)

# Клавиатуры

def get_auction_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("Copart", callback_data="copart"),
               InlineKeyboardButton("IAAI", callback_data="iaai"))
    return markup

def create_location_buttons(page=0, page_size=30):
    locations = list(delivery_dict.keys())
    page_locations = locations[page * page_size:(page + 1) * page_size]
    markup = InlineKeyboardMarkup(row_width=2)
    
    buttons = [InlineKeyboardButton(location, callback_data=f"loc_{location}") for location in page_locations]
    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i+2])  # отображать в 2 колонки

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page-1}"))
    if (page + 1) * page_size < len(locations):
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"page_{page+1}"))
    if nav_buttons:
        markup.row(*nav_buttons)

    return markup

def get_fuel_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    fuels = ["gasoline", "diesel", "hybrid", "electric"]
    for f in fuels:
        markup.add(InlineKeyboardButton(f.capitalize(), callback_data=f))
    return markup

def get_year_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for year in range(2010, 2026):
        buttons.append(InlineKeyboardButton(str(year), callback_data=f"year_{year}"))
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    return markup
    

def get_engine_volume_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    volumes = [1.0, 1.2, 1.4, 1.5, 1.6, 1.8, 2.0, 2.3, 2.4, 2.5, 2.7, 3.0, 3.2, 3.5, 3.7, 4.0, 4.4, 5.0, 6.7]
    buttons = [InlineKeyboardButton(str(v), callback_data=f"vol_{v}") for v in volumes]
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    return markup
    
def get_power_kw_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    for kw in range(30, 131, 10):
        markup.add(InlineKeyboardButton(f"{kw} кВт", callback_data=f"kw_{kw}"))
    return markup
    
# Обработчики
@dp.callback_query_handler(lambda c: c.data == "ask_expert")
async def handle_expert_request(call: types.CallbackQuery):
    user_data[call.from_user.id]["expecting_question"] = True
    await call.message.answer("✍️ Напишіть ваше питання, і експерт зв'яжеться з вами.")

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Привіт! Обери аукціон:", reply_markup=get_auction_keyboard())

@dp.callback_query_handler(lambda c: c.data in ['copart', 'iaai'])
async def choose_auction(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_data[user_id]['auction'] = call.data
    user_data[user_id]['edit_field'] = 'price'  # Активируем обработку ввода цены
    await call.message.answer("Введи ціну автомобіля в доларах:")

@dp.callback_query_handler(lambda c: c.data.startswith('page_'))
async def paginate_locations(call: types.CallbackQuery):
    page = int(call.data.split('_')[1])
    await call.message.edit_reply_markup(reply_markup=create_location_buttons(page))

@dp.callback_query_handler(lambda c: c.data.startswith('loc_'))
async def choose_location(call: types.CallbackQuery):
    user_id = call.from_user.id
    location = call.data[4:]
    user_data[user_id]['location'] = location
    user_data[user_id]['delivery_price'] = delivery_dict[location]

    required = ['price', 'location', 'fuel', 'year', 'engine_volume']
    if all(key in user_data[user_id] for key in required):
        result, breakdown = calculate_import(user_data[user_id])
        text_lines = []
        for k, v in breakdown.items():
            if isinstance(v, (int, float)):
                text_lines.append(f"{k}: ${v:.0f}")
            else:
                text_lines.append(f"{k}: {v}")
        text = "\n".join(text_lines)
        text += f"\n\n*Підсумкова сума:* ${result:.0f}"

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✏️ Ціна", callback_data="edit_price"),
            InlineKeyboardButton("📍 Локація", callback_data="edit_location"),
            InlineKeyboardButton("⚡ Пальне", callback_data="edit_fuel"),
            InlineKeyboardButton("📅 Рік", callback_data="edit_year"),
            InlineKeyboardButton("🛠 Обʼєм", callback_data="edit_volume"),
            InlineKeyboardButton("✏️ Експедитор", callback_data="edit_expeditor"),
            InlineKeyboardButton("✏️ Брокер", callback_data="edit_broker"),
            InlineKeyboardButton("✏️ Доставка в Україну", callback_data="edit_ukraine_delivery"),
            InlineKeyboardButton("✏️ Сертифікація", callback_data="edit_cert"),
            InlineKeyboardButton("✏️ Послуги компанії", callback_data="edit_stscars"),
            InlineKeyboardButton("📄 Згенерувати PDF", callback_data="generate_pdf"),
            InlineKeyboardButton("❓ Задати питання експерту", callback_data="ask_expert"),
            InlineKeyboardButton("📦 Почати з початку", callback_data="reset")
        )

        await call.message.answer(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await call.message.answer("Обери тип пального:", reply_markup=get_fuel_keyboard())

@dp.callback_query_handler(lambda c: c.data in ['gasoline', 'diesel', 'hybrid', 'electric'])
async def choose_fuel(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_data[user_id]['fuel'] = call.data

    required = ['price', 'location', 'fuel', 'year', 'engine_volume']
    if all(key in user_data[user_id] for key in required):
        result, breakdown = calculate_import(user_data[user_id])
        text_lines = []
        for k, v in breakdown.items():
            if isinstance(v, (int, float)):
                text_lines.append(f"{k}: ${v:.0f}")
            else:
                text_lines.append(f"{k}: {v}")
        text = "\n".join(text_lines)
        text += f"\n\n*Підсумкова сума:* ${result:.0f}"

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✏️ Ціна", callback_data="edit_price"),
            InlineKeyboardButton("📍 Локація", callback_data="edit_location"),
            InlineKeyboardButton("⚡ Пальне", callback_data="edit_fuel"),
            InlineKeyboardButton("📅 Рік", callback_data="edit_year"),
            InlineKeyboardButton("🛠 Обʼєм", callback_data="edit_volume"),
            InlineKeyboardButton("✏️ Експедитор", callback_data="edit_expeditor"),
            InlineKeyboardButton("✏️ Брокер", callback_data="edit_broker"),
            InlineKeyboardButton("✏️ Доставка в Україну", callback_data="edit_ukraine_delivery"),
            InlineKeyboardButton("✏️ Сертифікація", callback_data="edit_cert"),
            InlineKeyboardButton("✏️ Послуги компанії", callback_data="edit_stscars"),
            InlineKeyboardButton("📄 Згенерувати PDF", callback_data="generate_pdf"),
            InlineKeyboardButton("❓ Задати питання експерту", callback_data="ask_expert"),
            InlineKeyboardButton("📦 Почати з початку", callback_data="reset")
        )

        await call.message.answer(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await call.message.answer("Вибери рік випуску:", reply_markup=get_year_keyboard())
            
@dp.callback_query_handler(lambda c: c.data.startswith('year_'))
async def choose_year(call: types.CallbackQuery):
    user_id = call.from_user.id
    year = int(call.data[5:])
    user_data[user_id]['year'] = year

    fuel = user_data[user_id].get('fuel')

    required = ['price', 'location', 'fuel', 'year', 'engine_volume']
    if all(key in user_data[user_id] for key in required):
        result, breakdown = calculate_import(user_data[user_id])
        text_lines = []
        for k, v in breakdown.items():
            if isinstance(v, (int, float)):
                text_lines.append(f"{k}: ${v:.0f}")
            else:
                text_lines.append(f"{k}: {v}")
        text = "\n".join(text_lines)
        text += f"\n\n*Підсумкова сума:* ${result:.0f}"

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✏️ Ціна", callback_data="edit_price"),
            InlineKeyboardButton("📍 Локація", callback_data="edit_location"),
            InlineKeyboardButton("⚡ Пальне", callback_data="edit_fuel"),
            InlineKeyboardButton("📅 Рік", callback_data="edit_year"),
            InlineKeyboardButton("🛠 Обʼєм", callback_data="edit_volume"),
            InlineKeyboardButton("✏️ Експедитор", callback_data="edit_expeditor"),
            InlineKeyboardButton("✏️ Брокер", callback_data="edit_broker"),
            InlineKeyboardButton("✏️ Доставка в Україну", callback_data="edit_ukraine_delivery"),
            InlineKeyboardButton("✏️ Сертифікація", callback_data="edit_cert"),
            InlineKeyboardButton("✏️ Послуги компанії", callback_data="edit_stscars"),
            InlineKeyboardButton("📄 Згенерувати PDF", callback_data="generate_pdf"),
            InlineKeyboardButton("❓ Задати питання експерту", callback_data="ask_expert"),
            InlineKeyboardButton("📦 Почати з початку", callback_data="reset")
        )

        await call.message.answer(text, reply_markup=markup, parse_mode="Markdown")
    else:
        if fuel == 'electric':
            await call.message.answer("Обери потужність авто (кВт):", reply_markup=get_power_kw_keyboard())
        else:
            await call.message.answer("Обери обʼєм двигуна:", reply_markup=get_engine_volume_keyboard())
@dp.callback_query_handler(lambda c: c.data.startswith('vol_'))
async def choose_volume(call: types.CallbackQuery):
    try:
        volume = float(call.data[4:])
        user_id = call.from_user.id
        user_data[user_id]['engine_volume'] = volume

        # Расчёт
        result, breakdown = calculate_import(user_data[user_id])

        # Формируем текст результата
                # Формируем текст результата
        try:
            text_lines = []
            for k, v in breakdown.items():
                if "Год выпуска" in k or "Рік випуску" in k:
                    text_lines.append(f"{k}: {v}")
                elif isinstance(v, (int, float)):
                    text_lines.append(f"{k}: ${v:,.0f}")
                else:
                    text_lines.append(f"{k}: {v}")
            text = "\n".join(text_lines)
            text += f"\n\n*Підсумкова сума:* ${result:,.0f}"
        except Exception as e:
            await call.message.answer(f"Сталася помилка під час розрахунку:\n{e}")
            return
        # Кнопки редактирования
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✏️ Ціна", callback_data="edit_price"),
            InlineKeyboardButton("📍 Локація", callback_data="edit_location"),
            InlineKeyboardButton("⚡ Пальне", callback_data="edit_fuel"),
            InlineKeyboardButton("📅 Рік", callback_data="edit_year"),
            InlineKeyboardButton("🛠 Обʼєм", callback_data="edit_volume"),
            InlineKeyboardButton("✏️ Експедитор", callback_data="edit_expeditor"),
            InlineKeyboardButton("✏️ Брокер", callback_data="edit_broker"),
            InlineKeyboardButton("✏️ Доставка в Україну", callback_data="edit_ukraine_delivery"),
            InlineKeyboardButton("✏️ Сертифікація", callback_data="edit_cert"),
            InlineKeyboardButton("✏️ Послуги компанії", callback_data="edit_stscars"),
            InlineKeyboardButton("📄 Згенерувати PDF", callback_data="generate_pdf"),
            InlineKeyboardButton("❓ Задати питання експерту", callback_data="ask_expert"),
            InlineKeyboardButton("📦 Почати з початку", callback_data="reset")
        )

        await call.message.answer(text, reply_markup=markup, parse_mode="Markdown")

    except Exception as e:
        await call.message.answer(f"Сталася помилка під час розрахунку::\n`{e}`", parse_mode="Markdown")
        
@dp.callback_query_handler(lambda c: c.data.startswith('kw_'))
async def choose_power_kw(call: types.CallbackQuery):
    user_id = call.from_user.id
    power_kw = int(call.data[3:])
    user_data[user_id]['power_kw'] = power_kw

    required = ['price', 'location', 'fuel', 'year', 'power_kw']
    if all(key in user_data[user_id] for key in required):
        result, breakdown = calculate_import(user_data[user_id])

        def safe_get(key):
            return f"${breakdown.get(key, 0):,.0f}" if isinstance(breakdown.get(key), (int, float)) else breakdown.get(key, '-')

        text = f"""
**🚗 Ціна авто:** {safe_get('Ціна авто')}  
**🧾 Аукціонний збір:** {safe_get('Аукціонний збір')}  
**📍 Локація:** {safe_get('Локація')}  
**🚢 Доставка до Клайпеди:** {safe_get('Доставка до Клайпеди')}  
**💳 Комісія за інвойс (5%):** {safe_get('Комісія за оплату інвойсу (5%)')}  

**⚡ Тип пального:** {safe_get('Тип пального')}  
**🔋 Потужність / Обʼєм:** {safe_get('Обʼєм двигуна')}  
**📅 Рік випуску:** {safe_get('Рік випуску')}  

---

**🛃 Митні платежі:**  
**🔒 Ввізне мито (10%):** {safe_get('Ввізне мито (10%)')}  
**💥 Акциз:** {safe_get('Акциз (EUR, перерахований в USD)')}  
**🧾 ПДВ (20%)**: {safe_get('ПДВ (20%)')}  
**📦 Всього:** {safe_get('Митні платежі (всього)')}  

---

**💼 Додаткові витрати:**  
**🚛 Експедитор (Литва):** {safe_get('Експедитор (Литва)')}  
**🤝 Брокер:** {safe_get('Брокерські послуги')}  
**🚚 Доставка в Україну:** {safe_get('Доставка в Україну')}  
**🛠 Сертифікація:** {safe_get('Сертифікація')}  
**🏛 Пенсійний фонд:** {safe_get(next((k for k in breakdown if 'Пенсійний фонд' in k), 'Пенсійний фонд'))}  
**📄 МРЕВ:** $100  
**🏢 Послуги компанії:** {safe_get('Послуги компанії')}  

---

**✅ *Підсумкова сума:*** ${result:,.0f}
"""

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✏️ Ціна", callback_data="edit_price"),
            InlineKeyboardButton("📍 Локація", callback_data="edit_location"),
            InlineKeyboardButton("⚡ Пальне", callback_data="edit_fuel"),
            InlineKeyboardButton("⚡ Потужність (кВт)", callback_data="edit_volume"),
            InlineKeyboardButton("📅 Рік", callback_data="edit_year"),
            InlineKeyboardButton("✏️ Експедитор", callback_data="edit_expeditor"),
            InlineKeyboardButton("✏️ Брокер", callback_data="edit_broker"),
            InlineKeyboardButton("✏️ Доставка в Україну", callback_data="edit_ukraine_delivery"),
            InlineKeyboardButton("✏️ Сертифікація", callback_data="edit_cert"),
            InlineKeyboardButton("✏️ Послуги компанії", callback_data="edit_stscars"),
            InlineKeyboardButton("📄 Згенерувати PDF", callback_data="generate_pdf"),
            InlineKeyboardButton("❓ Задати питання експерту", callback_data="ask_expert"),
            InlineKeyboardButton("📦 Почати з початку", callback_data="reset")
        )

        await call.message.answer(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await call.message.answer("Недостатньо даних для розрахунку.")
# Функция расчета импортных пошлин и стоимости

def calculate_import(data):
    expeditor = data.get('expeditor', 350)
    broker = data.get('broker', 150)
    delivery_ua = data.get('delivery_ua', 1000)
    cert = data.get('cert', 150)
    stscars = data.get('stscars', 0)

    price = data['price']
    year = data['year']
    fuel = data['fuel']
    is_electric = fuel == 'electric'
    location = data['location']
    auction = data['auction']

    euro_to_usd_fixed = 1.1

    # Правильный возраст авто
    if year >= 2023:
        age = 1
    else:
        age = 2024 - year

    # Сбор аукциона
    auction_fee = get_auction_fee(auction, price)

    # Доставка
    delivery = data['delivery_price'] + (125 if fuel in ['electric', 'hybrid'] else 0)

    # Таможенная стоимость (цена авто + сбор + доставка в Клайпеду + 1600)
    customs_base = price + auction_fee + 1600
    invoice_fee = (price + auction_fee + delivery_dict[location]) * 0.05

    # Электро: мощность в кВт
    if is_electric:
        power_kw = data.get('power_kw', 0)
        excise_eur = power_kw * 1.1
        excise = excise_eur * euro_to_usd_fixed
        import_duty = 0
        vat = 0
        pension = 0
        volume_display = f"{power_kw} кВт"
    else:
        volume = data['engine_volume']
        volume_display = f"{volume} л"

        if fuel in ['hybrid', 'gasoline']:
            rate = 50 if volume <= 3.0 else 100
            excise_eur = rate * volume * age
        elif fuel == 'diesel':
            rate = 75 if volume <= 3.5 else 150
            excise_eur = rate * volume * age
        else:
            excise_eur = 0

        excise = excise_eur * euro_to_usd_fixed
        import_duty = customs_base * 0.10
        vat = (customs_base + import_duty + excise) * 0.20

        grn_price = customs_base * 40.5
        if grn_price < 499620:
            pension_percent = 0.03
        elif grn_price <= 878120:
            pension_percent = 0.04
        else:
            pension_percent = 0.05
        pension = customs_base * pension_percent

    total = price + auction_fee + delivery + import_duty + excise + vat + \
            expeditor + broker + delivery_ua + cert + pension + 100 + invoice_fee + stscars
    tamozhnya_total = import_duty + excise + vat

    breakdown = {
        'Ціна авто': price,
        'Аукціонний збір': auction_fee,
        'Локація': location,
        'Доставка до Клайпеди': delivery,
        'Комісія за оплату інвойсу (5%)': invoice_fee,
        'Тип пального': fuel.capitalize(),
        'Обʼєм двигуна': volume_display,
        'Рік випуску': year,
        'Ввізне мито (10%)': import_duty,
        'Акциз (EUR, перерахований в USD)': excise,
        'ПДВ (20%)': vat,
        'Митні платежі (всього)': tamozhnya_total,
        'Експедитор (Литва)': expeditor,
        'Брокерські послуги': broker,
        'Доставка в Україну': delivery_ua,
        'Сертифікація': cert,
        'Пенсійний фонд': pension,
        'МРЕВ (постановка на облік)': 50,
        'Послуги компанії': stscars,
    }

    return total, breakdown

# Получение сбора аукциона по цене

def get_auction_fee(auction, price):
    fees = iaai_fee_data if auction == 'iaai' else copart_fee_data
    for entry in fees:
        if entry['min'] <= price <= entry['max']:
            return entry.get('fee', round(price * entry.get('percent', 0), 2))
    return 0
# === Обработчик редактирования шагов ===
@dp.callback_query_handler(lambda c: c.data.startswith('edit_'))
async def edit_field(call: types.CallbackQuery):
    user_id = call.from_user.id
    action = call.data

    field_map = {
        "edit_price": ("Введи нову ціну:", "price"),
        "edit_location": ("Оберіть нову локацію:", "location"),
        "edit_fuel": ("Оберіть тип пального:", "fuel"),
        "edit_year": ("Оберіть рік випуску:", "year"),
        "edit_volume": ("Оберіть обʼєм двигуна:", "engine_volume"),
        "edit_expeditor": ("Введіть суму за експедитора:", "expeditor"),
        "edit_broker": ("Введіть суму за брокерські послуги:", "broker"),
        "edit_ukraine_delivery": ("Введіть вартість доставки в Україну:", "delivery_ua"),
        "edit_cert": ("Введіть вартість сертифікації:", "cert"),
        "edit_stscars": ("Введіть вартість послуг компанії:", "stscars")
    }

    if action in field_map:
        prompt, field = field_map[action]

        # Если поле требует клавиатуру (топливо, год, объём, локация) — показать нужную клавиатуру
        if field == "fuel":
            await call.message.answer(prompt, reply_markup=get_fuel_keyboard())
        elif field == "year":
            await call.message.answer(prompt, reply_markup=get_year_keyboard())
        elif field == "engine_volume":
            await call.message.answer(prompt, reply_markup=get_engine_volume_keyboard())
        elif field == "location":
            await call.message.answer(prompt, reply_markup=create_location_buttons())
        else:
            await call.message.answer(prompt)

        user_data[user_id]['edit_field'] = field
@dp.callback_query_handler(lambda c: c.data == 'reset')
async def reset_data(call: types.CallbackQuery):
    user_data.pop(call.from_user.id, None)
    await call.message.answer("Почнемо спочатку. Обери аукціон:", reply_markup=get_auction_keyboard())

@dp.message_handler(lambda msg: msg.text.replace('.', '', 1).isdigit())
async def handle_numeric_input(msg: types.Message):
    user_id = msg.from_user.id
    value = float(msg.text)

    if 'edit_field' in user_data[user_id]:
        field = user_data[user_id].pop('edit_field')
        user_data[user_id][field] = value

        # Переход к следующему этапу по порядку
        if field == 'price':
            await msg.answer("Оберіть локацію:", reply_markup=create_location_buttons())
        elif field == 'delivery_price':
            await msg.answer("Оберіть тип пального:", reply_markup=get_fuel_keyboard())
        elif field == 'fuel':
            await msg.answer("Оберіть рік випуску:", reply_markup=get_year_keyboard())
        elif field == 'year':
            await msg.answer("Оберіть обʼєм двигуна:", reply_markup=get_engine_volume_keyboard())
        elif field == 'engine_volume':
    # Дальше по коду...
            # Если всё заполнено — делаем расчёт
            required = ['price', 'location', 'fuel', 'year', 'engine_volume']
            if all(key in user_data[user_id] for key in required):
                result, breakdown = calculate_import(user_data[user_id])
                text_lines = []
                for k, v in breakdown.items():
                    if isinstance(v, (int, float)):
                        text_lines.append(f"{k}: ${v:.0f}")
                    else:
                        text_lines.append(f"{k}: {v}")
                text = "\n".join(text_lines)
                text += f"\n\n*Итоговая сумма:* ${result:.0f}"

                markup = InlineKeyboardMarkup(row_width=2)
                markup.add(
            InlineKeyboardButton("✏️ Ціна", callback_data="edit_price"),
            InlineKeyboardButton("📍 Локація", callback_data="edit_location"),
            InlineKeyboardButton("⚡ Пальне", callback_data="edit_fuel"),
            InlineKeyboardButton("📅 Рік", callback_data="edit_year"),
            InlineKeyboardButton("🛠 Обʼєм", callback_data="edit_volume"),
            InlineKeyboardButton("✏️ Експедитор", callback_data="edit_expeditor"),
            InlineKeyboardButton("✏️ Брокер", callback_data="edit_broker"),
            InlineKeyboardButton("✏️ Доставка в Україну", callback_data="edit_ukraine_delivery"),
            InlineKeyboardButton("✏️ Сертифікація", callback_data="edit_cert"),
            InlineKeyboardButton("✏️ Послуги компанії", callback_data="edit_stscars"),
            InlineKeyboardButton("📄 Згенерувати PDF", callback_data="generate_pdf"),
            InlineKeyboardButton("❓ Задати питання експерту", callback_data="ask_expert"),
            InlineKeyboardButton("📦 Почати з початку", callback_data="reset")
        )
                await msg.answer(text, reply_markup=markup, parse_mode="Markdown")
        else:
            # Если это не один из этапов — просто обновим и посчитаем заново
            required = ['price', 'location', 'fuel', 'year', 'engine_volume']
            if all(key in user_data[user_id] for key in required):
                result, breakdown = calculate_import(user_data[user_id])
                text_lines = []
                for k, v in breakdown.items():
                    if isinstance(v, (int, float)):
                        text_lines.append(f"{k}: ${v:.0f}")
                    else:
                        text_lines.append(f"{k}: {v}")
                text = "\n".join(text_lines)
                text += f"\n\n*Підсумкова сума:* ${result:.0f}"

                markup = InlineKeyboardMarkup(row_width=2)
                markup.add(
            InlineKeyboardButton("✏️ Ціна", callback_data="edit_price"),
            InlineKeyboardButton("📍 Локація", callback_data="edit_location"),
            InlineKeyboardButton("⚡ Пальне", callback_data="edit_fuel"),
            InlineKeyboardButton("📅 Рік", callback_data="edit_year"),
            InlineKeyboardButton("🛠 Обʼєм", callback_data="edit_volume"),
            InlineKeyboardButton("✏️ Експедитор", callback_data="edit_expeditor"),
            InlineKeyboardButton("✏️ Брокер", callback_data="edit_broker"),
            InlineKeyboardButton("✏️ Доставка в Україну", callback_data="edit_ukraine_delivery"),
            InlineKeyboardButton("✏️ Сертифікація", callback_data="edit_cert"),
            InlineKeyboardButton("✏️ Послуги компанії", callback_data="edit_stscars"),
            InlineKeyboardButton("📄 Згенерувати PDF", callback_data="generate_pdf"),
            InlineKeyboardButton("📦 Почати з початку", callback_data="reset")
        )
                await msg.answer(text, reply_markup=markup, parse_mode="Markdown")
@dp.callback_query_handler(lambda c: c.data == "generate_pdf")
async def send_pdf(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_data:
        await call.message.answer("Немає даних для генерації PDF.")
        return

    result, breakdown = calculate_import(user_data[user_id])
    auction = user_data[user_id].get("auction", "—")
    user_reports[user_id].append((result, breakdown))
    
    buffer = io.BytesIO()
    generate_import_pdf(breakdown, result, buffer, auction=auction)
    buffer.seek(0)
    buffer.name = "import_report.pdf"

    await bot.send_document(call.message.chat.id, InputFile(buffer))
@dp.message_handler(commands=["history"])
async def show_history(message: types.Message):
    user_id = message.from_user.id
    reports = user_reports.get(user_id, [])
    if not reports:
        await message.answer("Історія розрахунків порожня.")
        return

    text = ""
    for i, (res, data) in enumerate(reports, 1):
        text += f"<b>Розрахунок {i}</b>\n"
        for k, v in data.items():
            text += f"{k}: {v}\n"
        text += f"<b>До сплати:</b> ${res:,.0f}\n\n"

    await message.answer(text, parse_mode="HTML")
@dp.message_handler()
async def forward_to_expert(message: types.Message):
    user_id = message.from_user.id
    if user_data[user_id].get("expecting_question"):
        expert_chat_id = 422284478  # твой Telegram ID
        await bot.send_message(
            expert_chat_id,
            f"📩 Питання від @{message.from_user.username or message.from_user.full_name}:\n\n{message.text}"
        )
        await message.answer("✅ Ваше питання надіслано. Очікуйте на відповідь.")
        user_data[user_id]["expecting_question"] = False
        
# === Запуск бота ===
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
