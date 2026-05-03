import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ВСТАВЬТЕ ВАШ ТОКЕН
TOKEN = "8242359420:AAHmugElnTY4k2sq2nJMMUHx4olT8xjDvzA"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Главное меню ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚶‍♀️ Создать прогулку")],
        [KeyboardButton(text="📅 Смотреть прогулки")],
        [KeyboardButton(text="👤 Мои прогулки")],
        [KeyboardButton(text="📖 Правила"), KeyboardButton(text="🆘 Помощь")]
    ],
    resize_keyboard=True
)

walks = []
user_walks = {}
user_walk_index = {}
user_temp = {}

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот «Рядом».\n\n"
        "🚶‍♀️ Создать прогулку\n"
        "📅 Смотреть прогулки\n"
        "👤 Мои прогулки",
        reply_markup=main_kb
    )

@dp.message(lambda m: m.text == "📖 Правила")
async def show_rules(message: types.Message):
    await message.answer("📌 Правила сообщества...")

@dp.message(lambda m: m.text == "🆘 Помощь")
async def show_help(message: types.Message):
    await message.answer("🆘 Поддержка: @ryadom_poisk_support_bot")

@dp.message(lambda m: m.text == "🚶‍♀️ Создать прогулку")
async def create_walk_start(message: types.Message):
    user_temp[message.from_user.id] = {"step": "name"}
    await message.answer("Напишите название прогулки:")

@dp.message(lambda m: m.from_user.id in user_temp)
async def create_walk_collect(message: types.Message):
    user_id = message.from_user.id
    state = user_temp[user_id]
    step = state.get("step")

    if step == "name":
        state["name"] = message.text
        state["step"] = "place"
        await message.answer("📍 Напишите место сбора:")
    elif step == "place":
        state["place"] = message.text
        state["step"] = "datetime"
        await message.answer("🕓 Напишите дату и время (например: 15 мая, 18:30):")
    elif step == "datetime":
        state["datetime"] = message.text
        state["step"] = "max_members"
        await message.answer("👥 Максимум участников (0 — безлимит):")
    elif step == "max_members":
        state["max"] = message.text
        new_walk = {
            "id": len(walks) + 1,
            "name": state["name"],
            "place": state["place"],
            "datetime": state["datetime"],
            "max": state["max"],
            "creator": user_id,
            "members": [user_id]
        }
        walks.append(new_walk)
        if user_id not in user_walks:
            user_walks[user_id] = []
        user_walks[user_id].append(new_walk["id"])
        del user_temp[user_id]
        await message.answer("✅ Прогулка создана!", reply_markup=main_kb)

@dp.message(lambda m: m.text == "📅 Смотреть прогулки")
async def show_walks_start(message: types.Message):
    user_id = message.from_user.id
    available_walks = [walk for walk in walks]
    if not available_walks:
        await message.answer("Пока нет прогулок.")
        return
    user_walk_index[user_id] = {"walks": available_walks, "index": 0}
    await show_current_walk(message, user_id)

async def show_current_walk(message: types.Message, user_id: int):
    data = user_walk_index.get(user_id)
    if not data:
        return
    walks_list = data["walks"]
    current_idx = data["index"]
    if current_idx >= len(walks_list):
        await message.answer("Прогулки закончились.")
        del user_walk_index[user_id]
        return
    walk = walks_list[current_idx]
    text = f"📍 *{walk['name']}*\n🗓 {walk['datetime']}\n📍 {walk['place']}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Присоединиться", callback_data=f"join_{walk['id']}")],
        [InlineKeyboardButton(text="⏩ Дальше", callback_data="next_walk")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "next_walk")
async def next_walk(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = user_walk_index.get(user_id)
    if not data:
        await callback.answer("Список устарел.")
        await callback.message.delete()
        return
    await callback.message.delete()
    data["index"] += 1
    await show_current_walk(callback.message, user_id)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("join_"))
async def join_walk(callback: types.CallbackQuery):
    walk_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    for walk in walks:
        if walk["id"] == walk_id:
            if user_id in walk["members"]:
                await callback.answer("❌ Вы уже записаны!")
                return
            if walk["creator"] == user_id:
                await callback.answer("❌ Вы создатель!")
                return
            walk["members"].append(user_id)
            await callback.answer("✅ Вы записаны!")
            await callback.message.edit_text(callback.message.text + "\n\n✅ Вы идёте!", reply_markup=None)
            return
    await callback.answer("Прогулка не найдена!")

@dp.message(lambda m: m.text == "👤 Мои прогулки")
async def my_walks(message: types.Message):
    user_id = message.from_user.id
    my_list = [walk for walk in walks if user_id in walk["members"] or walk["creator"] == user_id]
    if not my_list:
        await message.answer("Вы не участвуете в прогулках.")
        return
    for walk in my_list:
        await message.answer(f"📍 {walk['name']}\n🗓 {walk['datetime']}\n📍 {walk['place']}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
