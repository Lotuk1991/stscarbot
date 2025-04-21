from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = '7772557710:AAE9YdvAK3rOr_BEFyV4grUx5l2nf8KybBs'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['lot'])
async def send_lot_info(message: types.Message):
    args = message.get_args()
    if not args.isdigit():
        await message.reply("Пожалуйста, укажите корректный номер лота.")
        return

    lot_id = args
    data = await fetch_lot_data(lot_id)

    if "error" in data:
        await message.reply(f"Ошибка: {data['error']}")
    else:
        lot_details = data.get("data", {}).get("lotDetails", {})
        if not lot_details:
            await message.reply("Информация о лоте не найдена.")
            return

        # Извлечение необходимых данных
        make = lot_details.get("make", "N/A")
        model = lot_details.get("model", "N/A")
        year = lot_details.get("year", "N/A")
        fuel = lot_details.get("fuel", "N/A")
        engine = lot_details.get("engine", "N/A")
        transmission = lot_details.get("transmission", "N/A")
        odometer = lot_details.get("odometer", "N/A")
        location = lot_details.get("location", "N/A")

        # Формирование сообщения
        response = (
            f"📄 Информация о лоте {lot_id}:\n"
            f"Марка: {make}\n"
            f"Модель: {model}\n"
            f"Год: {year}\n"
            f"Топливо: {fuel}\n"
            f"Двигатель: {engine}\n"
            f"Коробка передач: {transmission}\n"
            f"Пробег: {odometer}\n"
            f"Местоположение: {location}"
        )

        await message.reply(response)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)