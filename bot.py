import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8242359420:AAHGrdoshJV4ioUTJJiAWxiSkQZCOoEynd4"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Создать прогулку")],
        [KeyboardButton(text="Смотреть прогулки")],
        [KeyboardButton(text="Мои прогулки")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я бот Рядом.\n\n"
        "Создать прогулку - пригласить других\n"
        "Смотреть прогулки - найти компанию",
        reply_markup=main_kb
    )

walks = []
user_temp = {}

@dp.message(lambda m: m.text == "Создать прогулку")
async def create_walk_start(message: types.Message):
    user_temp[message.from_user.id] = {}
    await message.answer("Напишите название прогулки:")

@dp.message(lambda m: m.from_user.id in user_temp)
async def create_walk_collect(message: types.Message):
    user_id = message.from_user.id
    step = len(user_temp[user_id])

    if step == 0:
        user_temp[user_id]["name"] = message.text
        await message.answer("Напишите место сбора:")
    elif step == 1:
        user_temp[user_id]["place"] = message.text
        await message.answer("Напишите дату и время:")
    elif step == 2:
        user_temp[user_id]["datetime"] = message.text
        await message.answer("Максимум участников (0 - безлимит):")
    elif step == 3:
        user_temp[user_id]["max"] = message.text
        walks.append({
            "id": len(walks) + 1,
            "name": user_temp[user_id]["name"],
            "place": user_temp[user_id]["place"],
            "datetime": user_temp[user_id]["datetime"],
            "max": user_temp[user_id]["max"],
            "creator": user_id
        })
        await message.answer("Прогулка создана!", reply_markup=main_kb)
        del user_temp[user_id]

@dp.message(lambda m: m.text == "Смотреть прогулки")
async def show_walks(message: types.Message):
    if not walks:
        await message.answer("Пока нет прогулок. Создайте первую!")
        return
    for walk in walks:
        text = walk['name'] + "\n" + walk['place'] + "\n" + walk['datetime']
        await message.answer(text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

