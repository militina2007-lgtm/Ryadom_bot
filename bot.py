import asyncio
import logging
import re
from datetime import datetime
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

# --- Хранилище ---
walks = []
user_walks = {}
user_walk_index = {}
user_temp = {}

# --- Функция проверки даты ---
def parse_datetime(date_string):
    pattern = r'^(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря),\s+(\d{1,2}):(\d{2})$'
    match = re.match(pattern, date_string.strip())
    if not match:
        return None
    
    day = int(match.group(1))
    month_name = match.group(2)
    hour = int(match.group(3))
    minute = int(match.group(4))
    
    month_map = {
        "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
        "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
    }
    month = month_map.get(month_name.lower())
    if not month:
        return None
    
    try:
        current_year = datetime.now().year
        dt = datetime(current_year, month, day, hour, minute)
        return dt
    except ValueError:
        return None

def is_expired(datetime_str):
    dt = parse_datetime(datetime_str)
    if dt is None:
        return True
    return dt < datetime.now()

def clean_expired_walks():
    global walks, user_walks
    expired_ids = []
    for walk in walks:
        if is_expired(walk["datetime"]):
            expired_ids.append(walk["id"])
    
    if expired_ids:
        walks = [walk for walk in walks if walk["id"] not in expired_ids]
        for user in user_walks:
            user_walks[user] = [wid for wid in user_walks[user] if wid not in expired_ids]

def has_free_spots(walk):
    max_members = int(walk["max"]) if walk["max"].isdigit() else 0
    if max_members == 0:
        return True
    return len(walk["members"]) < max_members

# --- Команда /start ---
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Я — «Рядом».\n"
        "Я здесь, чтобы прогулки стали интереснее, а компании находились проще.\n\n"
        "🚶‍♀️ Создать прогулку — если хочешь позвать других\n"
        "📅 Смотреть прогулки — если ищешь, куда пойти\n"
        "👤 Мои прогулки — где ты участвуешь\n"
        "📖 Правила — безопасность и этика в нашем сообществе\n"
        "🆘 Помощь — если возникли вопросы\n\n"
        "Давай знакомиться?",
        reply_markup=main_kb
    )

# --- Правила ---
@dp.message(lambda m: m.text == "📖 Правила")
async def show_rules(message: types.Message):
    rules_text = (
        "📌 *Правила сообщества «Рядом»*\n\n"
        "1. Будьте вежливы друг с другом.\n\n"
        "2. Не опаздывайте без предупреждения.\n\n"
        "3. Если вы создали прогулку и передумали — удалите её.\n\n"
        "4. О конфликтах сообщайте в поддержку @ryadom_poisk_support_bot.\n\n"
        "5. Соблюдайте личные границы.\n\n"
        "6. Запрещена реклама, алкоголь, наркотики.\n\n"
        "🌿 Хороших прогулок!"
    )
    await message.answer(rules_text, parse_mode="Markdown")

# --- Помощь ---
@dp.message(lambda m: m.text == "🆘 Помощь")
async def show_help(message: types.Message):
    help_text = (
        "🆘 *Если у вас возник вопрос*, напишите в поддержку:\n\n"
        "📩 @ryadom_poisk_support_bot"
    )
    await message.answer(help_text, parse_mode="Markdown")

# --- Создание прогулки ---
@dp.message(lambda m: m.text == "🚶‍♀️ Создать прогулку")
async def create_walk_start(message: types.Message):
    user_temp[message.from_user.id] = {"step": "name"}
    await message.answer("🚶 Напишите название прогулки:")

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
        await message.answer("🕓 Напишите дату и время в формате: `15 мая, 18:30`", parse_mode="Markdown")
    elif step == "datetime":
        if parse_datetime(message.text) is None:
            await message.answer("❌ Неверный формат! Напишите: `15 мая, 18:30`", parse_mode="Markdown")
            return
        state["datetime"] = message.text
        state["step"] = "max_members"
        await message.answer("👥 Максимум участников (0 — безлимит):")
    elif step == "max_members":
        state["max"] = message.text
        confirm_text = (
            f"🧐 Проверьте прогулку:\n\n"
            f"📌 {state['name']}\n"
            f"📍 {state['place']}\n"
            f"🕓 {state['datetime']}\n"
            f"👥 Макс: {state['max'] if state['max'] != '0' else 'безлимит'}\n\n"
            f"✅ Всё верно?"
        )
        confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes")],
            [InlineKeyboardButton(text="✏️ Нет, исправить", callback_data="confirm_edit")]
        ])
        state["step"] = "confirm"
        await message.answer(confirm_text, reply_markup=confirm_kb)

@dp.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_walk(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_temp:
        await callback.answer("Ошибка!")
        return
    
    state = user_temp[user_id]
    
    if callback.data == "confirm_yes":
        new_walk = {
            "id": len(walks) + 1,
            "name": state["name"],
            "place": state["place"],
            "datetime": state["datetime"],
            "max": state["max"],
            "description": "",
            "creator": user_id,
            "members": [user_id]
        }
        walks.append(new_walk)
        
        if user_id not in user_walks:
            user_walks[user_id] = []
        user_walks[user_id].append(new_walk["id"])
        
        del user_temp[user_id]
        await callback.message.edit_text("✅ Прогулка создана!")
    else:
        state["step"] = "name"
        await callback.message.edit_text("✏️ Напишите новое название прогулки")
    
    await callback.answer()

# --- Смотреть прогулки (по одной) ---
@dp.message(lambda m: m.text == "📅 Смотреть прогулки")
async def show_walks_start(message: types.Message):
    user_id = message.from_user.id
    clean_expired_walks()
    
    available_walks = [walk for walk in walks if has_free_spots(walk)]
    
    if not available_walks:
        await message.answer("Пока нет доступных прогулок.")
        return
    
    user_walk_index[user_id] = {
        "walks": available_walks,
        "index": 0
    }
    
    await show_current_walk(message, user_id)

async def show_current_walk(message: types.Message, user_id: int, chat_id: int = None):
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
    
    current_members = len(walk["members"])
    max_members = int(walk["max"]) if walk["max"].isdigit() else 0
    members_text = f"{current_members}"
    if max_members > 0:
        members_text += f" / {max_members}"
    
    text = (
        f"📍 *{walk['name']}*\n"
        f"🗓 Когда: {walk['datetime']}\n"
        f"📍 Где: {walk['place']}\n"
        f"👥 Участников: {members_text}"
    )
    
    keyboard_buttons = [
        [InlineKeyboardButton(text="✅ Присоединиться", callback_data=f"join_{walk['id']}")]
    ]
    
    if current_idx + 1 < len(walks_list):
        keyboard_buttons.append([InlineKeyboardButton(text="⏩ Дальше", callback_data="next_walk")])
    else:
        keyboard_buttons.append([InlineKeyboardButton(text="🏁 Завершить", callback_data="end_walks")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "next_walk")
async def next_walk(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = user_walk_index.get(user_id)
    
    if not data:
        await callback.answer("Список устарел. Нажмите «Смотреть прогулки» заново.")
        await callback.message.delete()
        return
    
    # Удаляем текущее сообщение
    await callback.message.delete()
    
    data["index"] += 1
    await show_current_walk(callback.message, user_id, chat_id=callback.message.chat.id)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "end_walks")
async def end_walks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_walk_index:
        del user_walk_index[user_id]
    await callback.message.edit_text("🏁 Просмотр завершён.")
    await callback.answer()

# --- Присоединиться ---
@dp.callback_query(lambda c: c.data.startswith("join_"))
async def join_walk(callback: types.CallbackQuery):
    walk_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    walk = None
    for w in walks:
        if w["id"] == walk_id:
            walk = w
            break
    
    if not walk:
        await callback.answer("Прогулка не найдена!")
        return
    
    if walk["creator"] == user_id:
        await callback.answer("❌ Вы создатель!")
        return
    
    if user_id in walk["members"]:
        await callback.answer("❌ Вы уже записаны!")
        return
    
    if not has_free_spots(walk):
        await callback.answer("❌ Мест нет!")
        return
    
    walk["members"].append(user_id)
    
    if user_id not in user_walks:
        user_walks[user_id] = []
    if walk_id not in user_walks[user_id]:
        user_walks[user_id].append(walk_id)
    
    await callback.answer("✅ Вы записаны!")
    
    current_members = len(walk["members"])
    max_members = int(walk["max"]) if walk["max"].isdigit() else 0
    members_text = f"{current_members}"
    if max_members > 0:
        members_text += f" / {max_members}"
    
    new_text = (
        f"📍 *{walk['name']}*\n"
        f"🗓 {walk['datetime']}\n"
        f"📍 {walk['place']}\n"
        f"👥 {members_text}\n\n"
        f"✅ Вы записаны!"
    )
    
    await callback.message.edit_text(new_text, parse_mode="Markdown", reply_markup=None)

# --- Мои прогулки ---
@dp.message(lambda m: m.text == "👤 Мои прогулки")
async def my_walks(message: types.Message):
    user_id = message.from_user.id
    clean_expired_walks()
    
    my_walks_list = []
    for walk in walks:
        if user_id in walk["members"] or walk["creator"] == user_id:
            my_walks_list.append(walk)
    
    if not my_walks_list:
        await message.answer("Вы пока не участвуете в прогулках.")
        return
    
    for walk in my_walks_list:
        current_members = len(walk["members"])
        max_members = int(walk["max"]) if walk["max"].isdigit() else 0
        members_text = f"{current_members}"
        if max_members > 0:
            members_text += f" / {max_members}"
        
        creator_text = " (вы создатель)" if walk["creator"] == user_id else ""
        full_text = (
            f"📍 *{walk['name']}*{creator_text}\n"
            f"🗓 {walk['datetime']}\n"
            f"📍 {walk['place']}\n"
            f"👥 {members_text}"
        )
        
        if walk["creator"] == user_id:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{walk['id']}")]
            ])
            await message.answer(full_text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(full_text, parse_mode="Markdown")

# --- Удалить ---
@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_walk(callback: types.CallbackQuery):
    walk_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    walk_to_delete = None
    for walk in walks:
        if walk["id"] == walk_id:
            walk_to_delete = walk
            break
    
    if not walk_to_delete:
        await callback.answer("Не найдена!")
        return
    
    if walk_to_delete["creator"] != user_id:
        await callback.answer("Не ваша прогулка!")
        return
    
    walks[:] = [walk for walk in walks if walk["id"] != walk_id]
    
    for user in user_walks:
        if walk_id in user_walks[user]:
            user_walks[user].remove(walk_id)
    
    await callback.answer("Прогулка удалена!")
    await callback.message.edit_text(callback.message.text + "\n\n❌ Удалено", reply_markup=None)

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
