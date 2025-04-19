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

API_TOKEN = '7772557710:AAE9YdvAK3rOr_BEFyV4grUx5l2nf8KybBs'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_data = defaultdict(dict)
user_state = defaultdict(str)

with open('delivery_dict.json', 'r') as f:
    delivery_dict = json.load(f)
with open('copart_fee_data.json', 'r') as f:
    copart_fee_data = json.load(f)
with open('iaai_fee_data.json', 'r') as f:
    iaai_fee_data = json.load(f)

def get_auction_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Copart", callback_data="copart"),
        InlineKeyboardButton("IAAI", callback_data="iaai")
    )
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

def get_edit_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✏️ Изменить цену", callback_data="edit_price"),
        InlineKeyboardButton("📍 Изменить локацию", callback_data="edit_location"),
        InlineKeyboardButton("⚡ Изменить топливо", callback_data="edit_fuel"),
        InlineKeyboardButton("📅 Изменить год", callback_data="edit_year"),
        InlineKeyboardButton("🛠 Изменить объем", callback_data="edit_volume"),
        InlineKeyboardButton("🔁 Сбросить", callback_data="reset")
    )
    return markup
