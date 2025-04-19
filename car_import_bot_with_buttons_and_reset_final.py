from aiogram import Bot, Dispatcher, types, executor
import json
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = '7772557710:AAE9YdvAK3rOr_BEFyV4grUx5l2nf8KybBs'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

with open('iaai_fee_data.json') as f:
    iaai_fee_data = json.load(f)

with open('copart_fee_data.json') as f:
    copart_fee_data = json.load(f)

with open('delivery_dict.json') as f:
    delivery_prices = json.load(f)


    user_data = {}
    
    # Кнопки
    auction_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    auction_button_iaai = KeyboardButton("IAAI")
    auction_button_copart = KeyboardButton("Copart")
    auction_markup.add(auction_button_iaai, auction_button_copart)
    
    fuel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    fuel_markup.add(
        KeyboardButton("⛽ Бензин"),
        KeyboardButton("⚡ Електро"),
        KeyboardButton("🌀 Гібрид"),
        KeyboardButton("🛢️ Дизель")
    )
    
    volume_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    volumes = ['1.0', '1.2', '1.4', '1.5', '1.6', '1.8', '2.0', '2.2', '2.4', '2.5', '2.7', '3.0', '3.2', '3.5', '3.7', '4.0']
    volume_markup.add(*[KeyboardButton(volume) for volume in volumes])
    
    year_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    years = [str(year) for year in range(2005, 2025)]
    year_markup.add(*[KeyboardButton(year) for year in years])
    

def get_auction_fee(auction, price):
    data = iaai_fee_data if auction.upper() == "IAAI" else copart_fee_data
    for entry in data:
        if entry['min'] <= price <= entry['max']:
            if 'fee' in entry:
                return entry['fee']
            elif 'percent' in entry:
                return round(price * entry['percent'], 2)
    return 0

def search_delivery_locations(query):
    query = query.lower()
    return [city for city in delivery_prices if query in city.lower()][:10]

def calculate_customs(fuel, volume_liters, year, car_price, auction_fee):
    year = int(year)
    volume = float(volume_liters)
    age = max(1, 2025 - year)
    customs_base = car_price + auction_fee + 1600

    if fuel.lower() == "електро":
        excise = 100
        duty = 0
        vat = 0
    else:
        if fuel.lower() == "дизель":
            rate = 150 if volume > 3.5 else 75
        elif fuel.lower() in ["бензин", "гібрид"]:
            rate = 100 if volume > 3.0 else 50
        else:
            rate = 0
        excise = rate * age * volume
        duty = customs_base * 0.1
        vat = (customs_base + duty + excise) * 0.2

    return {
        "excise": round(excise, 2),
        "duty": round(duty, 2),
        "vat": round(vat, 2),
        "total": round(excise + duty + vat, 2)
    }

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_data[message.chat.id] = {}
    await message.answer("Привет! Выбери аукцион (Copart или IAAI):")

@dp.message_handler(lambda msg: msg.chat.id in user_data and 'auction' not in user_data[msg.chat.id])
async def auction_choice(message: types.Message):
    auction = message.text.strip().upper()
    if auction not in ["IAAI", "COPART"]:
        return await message.answer("Пожалуйста, введи Copart или IAAI.")
    user_data[message.chat.id]['auction'] = auction
    await message.answer("Введи стоимость автомобиля в долларах США:")

@dp.message_handler(lambda msg: msg.chat.id in user_data and 'price' not in user_data[msg.chat.id])
async def price_input(message: types.Message):
    try:
        price = float(message.text.strip())
        user_data[message.chat.id]['price'] = price
        await message.answer("Теперь введи локацию для доставки в Клайпеду (например: TX, CA, PERRIS):")
    except ValueError:
        await message.answer("Введите корректную числовую стоимость авто.")

@dp.message_handler(lambda msg: msg.chat.id in user_data and 'delivery_location' not in user_data[msg.chat.id])
async def delivery_location_handler(message: types.Message):
    query = message.text.strip()
    matches = search_delivery_locations(query)
    if not matches:
        return await message.answer("Не найдено подходящих площадок. Попробуйте другое название.")
    if len(matches) == 1:
        location = matches[0]
        user_data[message.chat.id]['delivery_location'] = location
        user_data[message.chat.id]['delivery_price'] = delivery_prices[location]
        await message.answer(f"Выбрана площадка: {location}\nСтоимость доставки в Клайпеду: ${delivery_prices[location]}")
        await message.answer("Укажи тип топлива (Бензин, Дизель, Гібрид, Електро):")
    else:
        reply_text = "Выбери одну площадку из списка:\n\n" + "\n".join(matches)
        await message.answer(reply_text)

@dp.message_handler(lambda msg: msg.chat.id in user_data and 'fuel' not in user_data[msg.chat.id])
async def save_fuel(message: types.Message):
    fuel = message.text.strip().capitalize()
    if fuel not in ["Бензин", "Дизель", "Гібрид", "Електро"]:
        return await message.answer("Введите корректный тип топлива.")
    user_data[message.chat.id]['fuel'] = fuel
    await message.answer("Укажи объем двигателя в литрах (например: 2.0):")

@dp.message_handler(lambda msg: msg.chat.id in user_data and 'volume' not in user_data[msg.chat.id])
async def save_volume(message: types.Message):
    try:
        volume = float(message.text.strip())
        user_data[message.chat.id]['volume'] = volume
        await message.answer("Укажи год выпуска авто:")
    except ValueError:
        await message.answer("Введите корректный объем двигателя.")

@dp.message_handler(lambda msg: msg.chat.id in user_data and 'year' not in user_data[msg.chat.id])
async def save_year(message: types.Message):
    try:
        year = int(message.text.strip())
        user_data[message.chat.id]['year'] = year
        await show_calculations(message)
    except ValueError:
        await message.answer("Введите корректный год, например: 2018")

async def show_calculations(message):
    data = user_data[message.chat.id]
    auction = data['auction']
    price = data['price']
    delivery_price = data['delivery_price']
    fuel = data['fuel']
    volume = data['volume']
    year = data['year']

    auction_fee = get_auction_fee(auction, price)
    payment_fee = round((price + auction_fee + delivery_price) * 0.05, 2)
    customs = calculate_customs(fuel, volume, year, price, auction_fee)

    expeditor = 500
    delivery_to_ua = 1000
    certification = 125
    mreo = 45
    stscars = 500

    customs_base = price + auction_fee + 1600
    if fuel.lower() == "електро":
        pension = 0
        pension_percent = 0
    elif customs_base < 11500:
        pension_percent = 3
    elif 11500 <= customs_base < 20000:
        pension_percent = 4
    else:
        pension_percent = 5
    pension = round(customs_base * (pension_percent / 100), 2)

    total = sum([
        price, auction_fee, payment_fee, delivery_price,
        customs['total'], expeditor, delivery_to_ua,
        certification, pension, mreo, stscars
    ])

    response = (
        f"📦 Расчёт импорта:\n\n"
        f"Аукцион: {auction}\n"
        f"Цена авто: ${price}\n"
        f"Сбор аукциона: ${auction_fee}\n"
        f"Комиссия за проплату: ${payment_fee}\n"
        f"Доставка в Клайпеду: ${delivery_price}\n\n"
        f"🚛 Растаможка:\n"
        f"Акциз: ${customs['excise']}\n"
        f"Мито: ${customs['duty']}\n"
        f"ПДВ: ${customs['vat']}\n"
        f"Итого: ${customs['total']}\n\n"
        f"📄 Доп. расходы:\n"
        f"Экспедитор: ${expeditor}\n"
        f"Доставка в Украину: ${delivery_to_ua}\n"
        f"Сертификация: ${certification}\n"
        f"Пенсионный фонд ({pension_percent}%): ${pension}\n"
        f"МРЕО: ${mreo}\n"
        f"STScars: ${stscars}\n\n"
        f"💰 Финально: *${round(total, 2)}*"
    )

    await message.answer(response, parse_mode="Markdown")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

# Кнопки для выбора аукциона
auction_markup = ReplyKeyboardMarkup(resize_keyboard=True)
auction_button_iaai = KeyboardButton("IAAI")
auction_button_copart = KeyboardButton("Copart")
auction_markup.add(auction_button_iaai, auction_button_copart)

# Кнопки для выбора года
year_markup = ReplyKeyboardMarkup(resize_keyboard=True)
years = [str(year) for year in range(2010, 2026)]  # Года с 2010 по 2025
year_markup.add(*[KeyboardButton(year) for year in years])

# Кнопки для выбора объема двигателя
volume_markup = ReplyKeyboardMarkup(resize_keyboard=True)
volumes = ['1.0', '1.2', '1.4', '1.5', '1.6', '1.8', '2.0', '2.2', '2.4', '2.5', '2.7', '3.0', '3.2', '3.5', '3.7', '4.7', '5.0', '4.0']
volume_markup.add(*[KeyboardButton(volume) for volume in volumes])

# Перезапуск бота
restart_markup = ReplyKeyboardMarkup(resize_keyboard=True)
restart_button = KeyboardButton("🔁 Почати спочатку")
restart_markup.add(restart_button)

# Обработка команды start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_data[message.chat.id] = {}  # Очистка данных пользователя
    await message.answer("Привіт! Обери аукціон (Copart або IAAI):", reply_markup=auction_markup)

# Выбор аукциона
@dp.message_handler(lambda msg: msg.chat.id in user_data and 'auction' not in user_data[msg.chat.id])
async def auction_choice(message: types.Message):
    auction = message.text.strip().upper()
    if auction not in ["IAAI", "COPART"]:
        return await message.answer("Пожалуйста, введи Copart або IAAI.")
    user_data[message.chat.id]['auction'] = auction
    await message.answer("Введи вартість автомобіля в доларах США:")

# Ввод стоимости авто
@dp.message_handler(lambda msg: msg.chat.id in user_data and 'price' not in user_data[msg.chat.id])
async def price_input(message: types.Message):
    try:
        price = float(message.text.strip())
        user_data[message.chat.id]['price'] = price
        await message.answer("Тепер введи локацію для доставки до Клайпеди (наприклад: TX, CA, PERRIS):")
    except ValueError:
        await message.answer("Введи коректну числову вартість авто.")

# Выбор типа топлива
fuel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
fuel_button_benzin = KeyboardButton("Бензин")
fuel_button_diesel = KeyboardButton("Дизель")
fuel_button_hybrid = KeyboardButton("Гібрид")
fuel_button_electro = KeyboardButton("Електро")
fuel_markup.add(fuel_button_benzin, fuel_button_diesel, fuel_button_hybrid, fuel_button_electro)

@dp.message_handler(lambda msg: msg.chat.id in user_data and 'price' in user_data[msg.chat.id] and 'fuel' not in user_data[msg.chat.id])
async def fuel_input(message: types.Message):
    await message.answer("Вибери тип пального:", reply_markup=fuel_markup)

# Выбор года
@dp.message_handler(lambda msg: msg.chat.id in user_data and 'fuel' in user_data[msg.chat.id] and 'year' not in user_data[msg.chat.id])
async def save_year(message: types.Message):
    await message.answer("Вибери рік випуску авто (2010–2025):", reply_markup=year_markup)

# Выбор объема двигателя
@dp.message_handler(lambda msg: msg.chat.id in user_data and 'year' in user_data[msg.chat.id] and 'volume' not in user_data[msg.chat.id])
async def save_volume(message: types.Message):
    await message.answer("Вибери обʼєм двигуна (1.0–5.0):", reply_markup=volume_markup)


# Выбор площадки с фильтрацией
@dp.message_handler(lambda msg: msg.chat.id in user_data and 'volume' in user_data[msg.chat.id] and 'delivery_location' not in user_data[msg.chat.id])
async def delivery_location_handler(message: types.Message):
    query = message.text.strip().lower()
    matches = [location for location in delivery_prices if query in location.lower()]
    
    if matches:
        location_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        location_markup.add(*[KeyboardButton(location) for location in matches[:10]])
        
        if len(matches) > 10:
            await message.answer("Знайдено кілька варіантів, вибери один з нижче:", reply_markup=location_markup)
        else:
            user_data[message.chat.id]['delivery_location'] = matches[0]
            user_data[message.chat.id]['delivery_price'] = delivery_prices[matches[0]]
            await message.answer(f"Вибрана площадка: {matches[0]}\nВартість доставки до Клайпеди: ${delivery_prices[matches[0]]}")
    else:
        await message.answer("Не знайдено підходящих варіантів. Спробуйте ввести іншу частину назви.")


# Завершение работы бота с кнопкой перезапуска
@dp.message_handler(lambda msg: msg.text == "🔁 Почати спочатку")
async def restart_handler(message: types.Message):
    user_data[message.chat.id] = {}
    await start_command(message)