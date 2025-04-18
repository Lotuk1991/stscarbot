import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor

API_TOKEN = '7772557710:AAE9YdvAK3rOr_BEFyV4grUx5l2nf8KybBs'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Загрузка данных о локациях и ценах из файла
with open('delivery_dict.json', 'r') as f:
    delivery_dict = json.load(f)

# Загрузка сборов для аукционов
with open('copart_fee_data.json', 'r') as f:
    copart_fee_data = json.load(f)

with open('iaai_fee_data.json', 'r') as f:
    iaai_fee_data = json.load(f)

# Клавиатура для выбора аукциона
auction_buttons = InlineKeyboardMarkup(row_width=2)
auction_button_copart = InlineKeyboardButton(text="Copart", callback_data="copart")
auction_button_iaai = InlineKeyboardButton(text="IAAI", callback_data="iaai")
auction_buttons.add(auction_button_copart, auction_button_iaai)

# Клавиатура для выбора локации
page_size = 10  # Количество локаций на странице
current_page = 0  # Текущая страница

def create_location_buttons(page=0):
    locations = list(delivery_dict.keys())
    page_locations = locations[page * page_size:(page + 1) * page_size]
    buttons = InlineKeyboardMarkup(row_width=2)
    
    for location in page_locations:
        buttons.add(InlineKeyboardButton(text=location, callback_data=location))
    
    # Кнопки для навигации по страницам
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"prev_{page-1}"))
    if (page + 1) * page_size < len(locations):
        navigation_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"next_{page+1}"))
    
    if navigation_buttons:
        buttons.add(*navigation_buttons)
    
    return buttons

# Клавиатура для выбора топлива
fuel_buttons = InlineKeyboardMarkup(row_width=2)
fuel_buttons.add(InlineKeyboardButton(text="Бензин", callback_data="gasoline"),
                 InlineKeyboardButton(text="Дизель", callback_data="diesel"),
                 InlineKeyboardButton(text="Гибрид", callback_data="hybrid"),
                 InlineKeyboardButton(text="Электро", callback_data="electric"))

# Клавиатура для выбора года выпуска
year_buttons = InlineKeyboardMarkup(row_width=3)
for year in range(2010, 2026):
    year_buttons.add(InlineKeyboardButton(text=str(year), callback_data=str(year)))

# Клавиатура для выбора объема двигателя
engine_volume_buttons = InlineKeyboardMarkup(row_width=3)
for volume in [1.0, 1.2, 1.5, 1.6, 2.0, 2.5, 3.0, 3.5, 4.0]:
    engine_volume_buttons.add(InlineKeyboardButton(text=str(volume), callback_data=str(volume)))

# Состояния
user_data = {}

# Стартовое сообщение
@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Привет! Выбери аукцион (Copart или IAAI):", reply_markup=auction_buttons)

# Обработка выбора аукциона
@dp.callback_query_handler(lambda c: c.data == 'copart' or c.data == 'iaai')
async def auction_chosen(callback_query: types.CallbackQuery):
    user_data[callback_query.from_user.id]['auction'] = callback_query.data
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Теперь введи стоимость автомобиля в долларах:")

# Обработка стоимости автомобиля
@dp.message_handler(lambda message: message.text.isdigit())
async def price_chosen(message: types.Message):
    user_data[message.from_user.id]['price'] = int(message.text)
    await message.answer("Теперь выбери локацию для доставки в Клайпеду:", reply_markup=create_location_buttons())

# Обработка навигации по локациям
@dp.callback_query_handler(lambda c: c.data.startswith('prev_') or c.data.startswith('next_'))
async def location_pagination(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split('_')[1])
    user_data[callback_query.from_user.id]['page'] = page
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"Выберите локацию для доставки в Клайпеду:", reply_markup=create_location_buttons(page))

# Обработка выбора локации
@dp.callback_query_handler(lambda c: c.data in delivery_dict)
async def location_chosen(callback_query: types.CallbackQuery):
    user_data[callback_query.from_user.id]['location'] = callback_query.data
    user_data[callback_query.from_user.id]['delivery_price'] = delivery_dict[callback_query.data]
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"Вы выбрали локацию {callback_query.data} с ценой доставки {delivery_dict[callback_query.data]}$. Теперь выбери тип топлива:", reply_markup=fuel_buttons)

# Обработка выбора топлива
@dp.callback_query_handler(lambda c: c.data in ['gasoline', 'diesel', 'hybrid', 'electric'])
async def fuel_chosen(callback_query: types.CallbackQuery):
    user_data[callback_query.from_user.id]['fuel'] = callback_query.data
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Теперь выбери год выпуска автомобиля:", reply_markup=year_buttons)

# Обработка года выпуска
@dp.callback_query_handler(lambda c: c.data.isdigit())
async def year_chosen(callback_query: types.CallbackQuery):
    user_data[callback_query.from_user.id]['year'] = int(callback_query.data)
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Теперь выбери объем двигателя:", reply_markup=engine_volume_buttons)

# Обработка объема двигателя
@dp.callback_query_handler(lambda c: c.data.replace('.', '', 1).isdigit())
async def engine_volume_chosen(callback_query: types.CallbackQuery):
    user_data[callback_query.from_user.id]['engine_volume'] = float(callback_query.data)
    await bot.answer_callback_query(callback_query.id)

    # Расчёт итоговой стоимости
    total_cost, additional_fees = calculate_import(user_data[callback_query.from_user.id])

    # Заменяем тип топлива на русский
    fuel_type = user_data[callback_query.from_user.id]['fuel']
    if fuel_type == "gasoline":
        fuel_type = "Бензин"
    elif fuel_type == "diesel":
        fuel_type = "Дизель"
    elif fuel_type == "hybrid":
        fuel_type = "Гибрид"
    elif fuel_type == "electric":
        fuel_type = "Электро"

    # Получаем цену доставки
    delivery_price = user_data[callback_query.from_user.id]['delivery_price']

    # Сбор аукциона
    auction_fee = get_auction_fee(user_data[callback_query.from_user.id]['auction'], user_data[callback_query.from_user.id]['price'])

    result_message = f"Расчёт импорта:\n\n" \
                     f"Аукцион: {user_data[callback_query.from_user.id]['auction']}\n" \
                     f"Цена авто: ${user_data[callback_query.from_user.id]['price']}\n" \
                     f"Тип топлива: {fuel_type}\n" \
                     f"Локация: {user_data[callback_query.from_user.id]['location']}\n" \
                     f"Стоимость доставки в Клайпеду: ${delivery_price}\n" \
                     f"Сбор аукциона: ${auction_fee}\n" \
                     f"Год выпуска: {user_data[callback_query.from_user.id]['year']}\n" \
                     f"Объем двигателя: {user_data[callback_query.from_user.id]['engine_volume']} литров\n\n" \
                     f"Итоговая сумма: ${total_cost}\n" \
                     f"Доп. расходы: {additional_fees}\n\n" \
                     f"Для сброса данных, нажми кнопку ниже."

    reset_button = InlineKeyboardButton(text="Сбросить данные", callback_data="reset")
    reset_markup = InlineKeyboardMarkup().add(reset_button)

    await bot.send_message(callback_query.from_user.id, result_message, reply_markup=reset_markup)

# Функция расчёта
def calculate_import(user_info):
    # Расчет сборов на основе аукциона
    auction_fee = get_auction_fee(user_info["auction"], user_info["price"])

    # Примерные значения для расчета (можно адаптировать в зависимости от ваших данных)
    delivery_fee = user_info["delivery_price"]  # Цена доставки из локации
    customs_duty = 0.2 * user_info["price"]  # Таможенная пошлина (20% от цены авто)
    vat = 0.2 * (user_info["price"] + customs_duty)  # НДС (20% от цены + таможенная пошлина)

    # Дополнительные расходы
    additional_fees = {"Экспедитор": 500, "Доставка в Украину": 1000, "Сертификация": 125, "Пенсионный фонд (3%)": 0.03 * user_info["price"]}
    total_additional_fees = sum(additional_fees.values())

    total_cost = user_info["price"] + auction_fee + customs_duty + vat + delivery_fee + total_additional_fees
    return total_cost, additional_fees

# Функция для получения сбора аукциона
def get_auction_fee(auction, price):
    fee_data = iaai_fee_data if auction == "IAAI" else copart_fee_data
    for entry in fee_data:
        if entry['min'] <= price <= entry['max']:
            if 'fee' in entry:
                return entry['fee']
            elif 'percent' in entry:
                return round(price * entry['percent'], 2)
    return 0

# Сброс данных
@dp.callback_query_handler(lambda c: c.data == 'reset')
async def reset_data(callback_query: types.CallbackQuery):
    user_data.clear()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Данные сброшены. Выберите аукцион снова:", reply_markup=auction_buttons)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
