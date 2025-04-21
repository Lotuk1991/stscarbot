import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import aiohttp

API_TOKEN = '7772557710:AAE9YdvAK3rOr_BEFyV4grUx5l2nf8KybBs'  # твой токен

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния
class ImportCarStates(StatesGroup):
    waiting_for_lot = State()

# Старт
@dp.message_handler(commands='start')
async def start_command(message: types.Message):
    await ImportCarStates.waiting_for_lot.set()
    await message.answer("Привіт! Введи номер лоту Copart:")

# Обработка номера лота
@dp.message_handler(lambda message: message.text.isdigit(), state=ImportCarStates.waiting_for_lot)
async def process_lot(message: types.Message, state: FSMContext):
    lot_id = message.text.strip()
    await message.answer("⏳ Отримую інформацію з Copart...")

    data = await fetch_lot_data(lot_id)

    if "error" in data:
        await message.answer(f"Помилка: {data['error']}")
    else:
        lot = data.get("data", {}).get("lotDetails", {})
        if not lot:
            await message.answer("Інформацію про лот не знайдено.")
            return

        make = lot.get("make", "N/A")
        model = lot.get("model", "N/A")
        year = lot.get("year", "N/A")
        fuel = lot.get("fuel", "N/A")
        engine = lot.get("engine", "N/A")
        odometer = lot.get("odometer", "N/A")
        location = lot.get("location", {}).get("name", "N/A")

        await message.answer(
            f"🔎 Інформація про лот {lot_id}:\n"
            f"Марка: {make}\n"
            f"Модель: {model}\n"
            f"Рік: {year}\n"
            f"Паливо: {fuel}\n"
            f"Двигун: {engine}\n"
            f"Пробіг: {odometer}\n"
            f"Локація: {location}"
        )

    await state.finish()

# API-запрос к Copart
async def fetch_lot_data(lot_id):
    url = f"https://www.copart.com/public/data/lotdetails/solr/{lot_id}/USA"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {"error": f"HTTP {response.status}"}

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)