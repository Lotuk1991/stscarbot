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
user_state = defaultdict(str)  # для отслеживания этапов

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
    user_state[message.from_user.id] = ''
    await message.answer("Привет! Выбери аукцион:", reply_markup=get_auction_keyboard())

@dp.callback_query_handler(lambda c: c.data in ['copart', 'iaai'])
async def choose_auction(call: types.CallbackQuery):
    user_data[call.from_user.id]['auction'] = call.data
    await call.message.answer("Введи цену автомобиля в долларах:")

@dp.message_handler(lambda msg: msg.text.replace('.', '', 1).isdigit())
async def handle_numeric_input(msg: types.Message):
    user_id = msg.from_user.id
    if user_state[user_id] == 'editing_price':
        user_data[user_id]['price'] = float(msg.text)
        user_state[user_id] = ''
        result, breakdown = calculate_import(user_data[user_id])
        text_lines = []
        for k, v in breakdown.items():
            if "Год выпуска" in k:
                text_lines.append(f"*{k}*: {v}")
            elif isinstance(v, (int, float)):
                text_lines.append(f"*{k}*: `${v:,.2f}`")
            else:
                text_lines.append(f"*{k}*: {v}")
        text = "\n".join(text_lines)
        text += f"\n\n*Итоговая сумма*: `${result:,.2f}`"
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔁 Сбросить", callback_data="reset"),
            InlineKeyboardButton("✏️ Изменить цену", callback_data="edit_price")
        )
        await msg.answer(text, parse_mode="Markdown", reply_markup=markup)
        return

    elif user_state[user_id] == 'waiting_for_battery':
        user_data[user_id]['battery_capacity'] = float(msg.text)
        user_state[user_id] = ''  # сброс состояния
        result, breakdown = calculate_import(user_data[user_id])
        await send_result(msg, user_id, result, breakdown)
        return
        await msg.answer("Выбери год выпуска:", reply_markup=get_year_keyboard())
    elif user_state[user_id] == 'editing_price':
        user_data[user_id]['price'] = float(msg.text)
        user_state[user_id] = ''
        result, breakdown = calculate_import(user_data[user_id])
        await send_result(msg, user_id, result, breakdown)
    else:
        user_data[user_id]['price'] = float(msg.text)
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
    fuel = call.data
    user_data[call.from_user.id]['fuel'] = fuel
    if fuel == 'electric':
        user_state[call.from_user.id] = 'waiting_for_battery'
        await call.message.answer("Введи емкость батареи в кВт⋅ч:")
    else:
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

        required_fields = ['price', 'fuel', 'year', 'engine_volume', 'auction', 'location', 'delivery_price']
        missing = [field for field in required_fields if field not in user_data[user_id]]
        if user_data[user_id].get('fuel') == 'electric' and 'battery_capacity' not in user_data[user_id]:
            missing.append('battery_capacity')

        if missing:
            await call.message.answer(f"Отсутствуют данные: {', '.join(missing)}. Начни заново с /start.")
            return

        result, breakdown = calculate_import(user_data[user_id])

        text_lines = []
        for k, v in breakdown.items():
            if "Год выпуска" in k:
                text_lines.append(f"*{k}*: {v}")
            elif isinstance(v, (int, float)):
                text_lines.append(f"*{k}*: `${v:,.2f}`")
            else:
                text_lines.append(f"*{k}*: {v}")
        text = "\n".join(text_lines)
        text += f"\n\n*Итоговая сумма*: `${result:,.2f}`"

        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("