# Импорт необходимых библиотек
import os
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict

# Логирование
logging.basicConfig(level=logging.INFO)

# Токен бота из переменной окружения
API_TOKEN = '7772557710:AAE9YdvAK3rOr_BEFyV4grUx5l2nf8KybBs'  # временно открытый токен

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хранилище пользовательских данных
user_data = defaultdict(dict)

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
    for location in page_locations:
        markup.add(InlineKeyboardButton(location, callback_data=f"loc_{location}"))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page-1}"))
    if (page + 1) * page_size < len(locations):
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"page_{page+1}"))
    if nav_buttons:
        markup.add(*nav_buttons)
    return markup

def get_fuel_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    fuels = ["gasoline", "diesel", "hybrid", "electric"]
    for f in fuels:
        markup.add(InlineKeyboardButton(f.capitalize(), callback_data=f))
    return markup

def get_year_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    for year in range(2010, 2026):
        markup.add(InlineKeyboardButton(str(year), callback_data=f"year_{year}"))
    return markup

def get_engine_volume_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    for volume in [1.0, 1.2, 1.5, 1.6, 2.0, 2.5, 3.0, 3.5, 4.0]:
        markup.add(InlineKeyboardButton(str(volume), callback_data=f"vol_{volume}"))
    return markup

# Обработчики

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Привет! Выбери аукцион:", reply_markup=get_auction_keyboard())

@dp.callback_query_handler(lambda c: c.data in ['copart', 'iaai'])
async def choose_auction(call: types.CallbackQuery):
    user_data[call.from_user.id]['auction'] = call.data
    await call.message.answer("Введи цену автомобиля в долларах:")

@dp.message_handler(lambda msg: msg.text.replace('.', '', 1).isdigit())
async def enter_price(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]['price'] = float(msg.text)

    # Если у пользователя уже есть всё остальное — сразу считаем
    required = ['price', 'location', 'fuel', 'year', 'engine_volume']
    if all(key in user_data[user_id] for key in required):
        result, breakdown = calculate_import(user_data[user_id])
        text_lines = []
        for k, v in breakdown.items():
            if isinstance(v, (int, float)):
                text_lines.append(f"{k}: ${v:.2f}")
            else:
                text_lines.append(f"{k}: {v}")
        text = "\n".join(text_lines)
        text += f"\n\n*Итоговая сумма:* ${result:.2f}"

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✏️ Цена", callback_data="edit_price"),
            InlineKeyboardButton("📍 Локация", callback_data="edit_location"),
            InlineKeyboardButton("⚡ Топливо", callback_data="edit_fuel"),
            InlineKeyboardButton("📅 Год", callback_data="edit_year"),
            InlineKeyboardButton("🛠 Объём", callback_data="edit_volume"),
            InlineKeyboardButton("📦 Сбросить", callback_data="reset")
        )

        await msg.answer(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await msg.answer("Выбери локацию:", reply_markup=create_location_buttons())
@dp.callback_query_handler(lambda c: c.data.startswith('page_'))
async def paginate_locations(call: types.CallbackQuery):
    page = int(call.data.split('_')[1])
    await call.message.edit_reply_markup(reply_markup=create_location_buttons(page))

@dp.callback_query_handler(lambda c: c.data.startswith('loc_'))
async def choose_location(call: types.CallbackQuery):
    location = call.data[4:]
    user_data[call.from_user.id]['location'] = location
    user_data[call.from_user.id]['delivery_price'] = delivery_dict[location]
    await call.message.answer("Выбери тип топлива:", reply_markup=get_fuel_keyboard())

@dp.callback_query_handler(lambda c: c.data in ['gasoline', 'diesel', 'hybrid', 'electric'])
async def choose_fuel(call: types.CallbackQuery):
    user_data[call.from_user.id]['fuel'] = call.data
    await call.message.answer("Выбери год выпуска:", reply_markup=get_year_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('year_'))
async def choose_year(call: types.CallbackQuery):
    year = int(call.data[5:])
    user_data[call.from_user.id]['year'] = year
    await call.message.answer("Выбери объем двигателя:", reply_markup=get_engine_volume_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('vol_'))
async def choose_volume(call: types.CallbackQuery):
    try:
        volume = float(call.data[4:])
        user_id = call.from_user.id
        user_data[user_id]['engine_volume'] = volume

        # Расчёт
        result, breakdown = calculate_import(user_data[user_id])

        # Формируем текст результата
        text_lines = []
        for k, v in breakdown.items():
            if isinstance(v, (int, float)):
                text_lines.append(f"{k}: ${v:.2f}")
            else:
                text_lines.append(f"{k}: {v}")
        text = "\n".join(text_lines)
        text += f"\n\n*Итоговая сумма:* ${result:.2f}"

        # Кнопки редактирования
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✏️ Цена", callback_data="edit_price"),
            InlineKeyboardButton("📍 Локация", callback_data="edit_location"),
            InlineKeyboardButton("⚡ Топливо", callback_data="edit_fuel"),
            InlineKeyboardButton("📅 Год", callback_data="edit_year"),
            InlineKeyboardButton("🛠 Объём", callback_data="edit_volume"),
            InlineKeyboardButton("📦 Сбросить", callback_data="reset")
        )

        await call.message.answer(text, reply_markup=markup, parse_mode="Markdown")

    except Exception as e:
        await call.message.answer(f"Произошла ошибка при расчёте:\n`{e}`", parse_mode="Markdown")

# Функция расчета импортных пошлин и стоимости

def calculate_import(data):
    price = data['price']
    volume = data['engine_volume']
    year = data['year']
    fuel = data['fuel']
    age = 2025 - year
    auction_fee = get_auction_fee(data['auction'], price)

    # Таможенная стоимость (цена авто + сбор + доставка в Клайпеду + 1600)
    customs_base = price + auction_fee + 1600
    invoice_fee = (price + auction_fee + delivery_dict[data['location']]) * 0.05

    # Пенсионный фонд: зависит от таможенной стоимости
    if customs_base < 37440:
        pension_percent = 0.03
    elif customs_base <= 65800:
        pension_percent = 0.04
    else:
        pension_percent = 0.05

    # Акциз
    if fuel == 'electric':
        excise_eur = 1 * age
    elif fuel == 'hybrid':
        excise_eur = 100 * volume
    else:
        rate = 75 if fuel == 'gasoline' else 150
        excise_eur = rate * volume * age

    euro_to_usd_fixed = 1.1
    excise = excise_eur * euro_to_usd_fixed

    import_duty = customs_base * 0.10
    vat = (customs_base + import_duty + excise) * 0.20
    delivery = data['delivery_price'] + (125 if fuel in ['electric', 'hybrid'] else 0)
    pension = customs_base * pension_percent

    total = price + auction_fee + delivery + import_duty + excise + vat + 350 + 500 + 1000 + 150 + pension + 100 + invoice_fee + 500

    tamozhnya_total = import_duty + excise + vat

    breakdown = {

        'Цена авто': price,
        'Сбор аукциона': auction_fee,
        'Локация': data['location'],
        'Доставка в Клайпеду': delivery,
        'Тип топлива': fuel.capitalize(),
        'Объем двигателя': f"{volume} л",
        'Год выпуска': year,
        'Ввозная пошлина (10%)': import_duty,
        'Акциз (EUR, пересчитан в USD)': excise,
        'НДС (20%)': vat,
        'Таможенные платежи (итого)': tamozhnya_total,
        'Экспедитор (Литва)': 350,
        'Брокерские услуги': 500,
        'Доставка в Украину': 1000,
        'Сертификация': 150,
        f'Пенсионный фонд ({int(pension_percent*100)}%)': pension,
        'МРЭО (постановка на учет)': 100,
        'Комиссия за оплату инвойса (5%)': invoice_fee,
        'Услуги компании': 500
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

    if action == "edit_price":
        await call.message.answer("Введи новую цену:")
    elif action == "edit_location":
        await call.message.answer("Выбери новую локацию:", reply_markup=create_location_buttons())
    elif action == "edit_fuel":
        await call.message.answer("Выбери тип топлива:", reply_markup=get_fuel_keyboard())
    elif action == "edit_year":
        await call.message.answer("Выбери год выпуска:", reply_markup=get_year_keyboard())
    elif action == "edit_volume":
        await call.message.answer("Выбери объем двигателя:", reply_markup=get_engine_volume_keyboard())

    field_map = {
        "edit_price": "price",
        "edit_location": "location",
        "edit_fuel": "fuel",
        "edit_year": "year",
        "edit_volume": "engine_volume"
    }
    field = field_map.get(action)
    if field:
        user_data[user_id].pop(field, None)


# === Запуск бота ===
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)