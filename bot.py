import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8242359420:AAHGrdoshJV4ioUTJJiAWxiSkQZCOoEynd4"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Главное меню (ДОБАВЛЕНА КНОПКА ПОМОЩЬ) ---
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

# --- ПРАВИЛА (с обновлённым контактом) ---
@dp.message(lambda m: m.text == "📖 Правила")
async def show_rules(message: types.Message):
    rules_text = (
        "📌 *Правила сообщества «Рядом»*\n\n"
        "1. Будьте вежливы друг с другом. Любое неуважительное поведение — повод исключить вас из сообщества.\n\n"
        "2. Не опаздывайте без предупреждения. Если вы не можете прийти — предупредите организатора или отмените участие.\n\n"
        "3. Если вы создали прогулку и передумали — удалите её через раздел «Мои прогулки». Не оставляйте людей в неопределённости.\n\n"
        "4. О любых конфликтных ситуациях (харассмент, токсичность, нарушение границ) сообщайте в поддержку @ryadom_poisk_support_bot.\n\n"
        "5. Соблюдайте личные границы других участников. Прогулка создаётся для общения и отдыха, а не для преследования.\n\n"
        "6. Запрещена реклама, флуд и спам в чатах и прогулках.\n\n"
        "7. Запрещены прогулки с целью употребления алкоголя или наркотиков.\n\n"
        "Нажимая «Присоединиться» или создавая прогулку, вы автоматически соглашаетесь с этими правилами.\n\n"
        "🌿 Берегите себя и друг друга. Хороших прогулок!"
    )
    await message.answer(rules_text, parse_mode="Markdown")

# --- ПОМОЩЬ ---
@dp.message(lambda m: m.text == "🆘 Помощь")
async def show_help(message: types.Message):
    help_text = (
        "🆘 *Если у вас возник какой-то вопрос*, напишите в поддержку, и мы постараемся вам помочь!\n\n"
        "📩 Контакт поддержки: @ryadom_poisk_support_bot\n\n"
        "Мы отвечаем как можно быстрее. Обычно в течение нескольких часов."
    )
    await message.answer(help_text, parse_mode="Markdown")

# --- Вспомогательная функция: проверка, есть ли места ---
def has_free_spots(walk):
    max_members = int(walk["max"]) if walk["max"].isdigit() else 0
    if max_members == 0:
        return True
    return len(walk["members"]) < max_members

# --- Создание прогулки ---
user_temp = {}

@dp.message(lambda m: m.text == "🚶‍♀️ Создать прогулку")
async def create_walk_start(message: types.Message):
    user_temp[message.from_user.id] = {"step": "name"}
    await message.answer(
        "🚶 Давайте создадим прогулку!\n\n"
        "Сначала придумайте название. Оно должно быть коротким, но понятным.\n\n"
        "Например: «Кофейный забег в центре» или «Медленный вечер в парке»\n\n"
        "➤ Напишите название прогулки"
    )

@dp.message(lambda m: m.from_user.id in user_temp)
async def create_walk_collect(message: types.Message):
    user_id = message.from_user.id
    state = user_temp[user_id]
    step = state.get("step")

    if step == "name":
        state["name"] = message.text
        state["step"] = "place"
        await message.answer(
            "📍 Отлично!\n\n"
            "Где встретимся? Напишите конкретное место, чтобы всем было легко найти друг друга.\n\n"
            "Например: «У центрального входа в парк Горького, у фонтана» или «Кофейня \"Кофе и точка\", Пушкина 10»\n\n"
            "➤ Укажите место сбора"
        )
    elif step == "place":
        state["place"] = message.text
        state["step"] = "datetime"
        await message.answer(
            "🕓 Теперь — когда гуляем?\n\n"
            "Напишите дату и время в правильном формате.\n\n"
            "Например:\n"
            "• 20 мая, 15:00\n\n"
            "➤ Укажите дату и время"
        )
    elif step == "datetime":
        state["datetime"] = message.text
        state["step"] = "description"
        await message.answer(
            "📝 Добавьте пару слов о прогулке (необязательно, но приятно).\n\n"
            "Например: «Забредём в три новые кофейни, возьмите с собой хорошее настроение 🐶 Можно с собаками»\n\n"
            "➤ Напишите описание или нажмите «Далее»",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⏩ Далее")]],
                resize_keyboard=True
            )
        )
    elif step == "description":
        if message.text != "⏩ Далее":
            state["description"] = message.text
        else:
            state["description"] = ""
        state["step"] = "max_members"
        await message.answer(
            "👥 Сколько человек может пойти?\n\n"
            "• 0 — безлимит\n"
            "• Число — например, 5\n\n"
            "➤ Укажите максимум участников",
            reply_markup=main_kb
        )
    elif step == "max_members":
        state["max"] = message.text
        confirm_text = (
            f"🧐 Проверьте прогулку перед публикацией:\n\n"
            f"📌 Название: {state['name']}\n"
            f"📍 Место: {state['place']}\n"
            f"🕓 Когда: {state['datetime']}\n"
            f"👥 Максимум участников: {state['max'] if state['max'] != '0' else 'безлимит'}\n"
            f"📝 Описание: {state['description'] if state['description'] else '—'}\n\n"
            f"✅ Всё верно?\n"
            f"✏️ Хочу исправить"
        )
        confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Всё верно", callback_data="confirm_yes")],
            [InlineKeyboardButton(text="✏️ Исправить", callback_data="confirm_edit")]
        ])
        state["step"] = "confirm"
        await message.answer(confirm_text, reply_markup=confirm_kb)

# --- Обработка подтверждения ---
@dp.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_walk(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_temp:
        await callback.answer("Ошибка! Начните создание заново.")
        return
    
    state = user_temp[user_id]
    
    if callback.data == "confirm_yes":
        new_walk = {
            "id": len(walks) + 1,
            "name": state["name"],
            "place": state["place"],
            "datetime": state["datetime"],
            "max": state["max"],
            "description": state.get("description", ""),
            "creator": user_id,
            "members": [user_id]
        }
        walks.append(new_walk)
        
        if user_id not in user_walks:
            user_walks[user_id] = []
        user_walks[user_id].append(new_walk["id"])
        
        del user_temp[user_id]
        await callback.message.edit_text(
            "✅ Прогулка опубликована!\n\n"
            "Теперь её увидят другие участники. Вы можете поделиться ссылкой на бота или дождаться, пока кто-то присоединится.\n\n"
            "➤ Прогулка появится в общем списке. Удачных вам встреч! 🌿"
        )
    else:
        state["step"] = "name"
        await callback.message.edit_text(
            "✏️ Давайте исправим.\n\n"
            "➤ Напишите новое название прогулки"
        )
    
    await callback.answer()

# --- Смотреть прогулки ---
@dp.message(lambda m: m.text == "📅 Смотреть прогулки")
async def show_walks(message: types.Message):
    available_walks = [walk for walk in walks if has_free_spots(walk)]
    
    if not available_walks:
        await message.answer("Пока нет доступных прогулок. Загляните позже или создайте свою!")
        return

    for walk in available_walks:
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
        if walk.get('description'):
            text += f"\n📝 {walk['description']}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Присоединиться", callback_data=f"join_{walk['id']}")]
        ])
        
        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

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
    
    if not has_free_spots(walk):
        await callback.answer("Мест больше нет!")
        return
    
    if user_id in walk["members"]:
        await callback.answer("Вы уже записаны на эту прогулку!")
        return
    
    walk["members"].append(user_id)
    
    if user_id not in user_walks:
        user_walks[user_id] = []
    if walk_id not in user_walks[user_id]:
        user_walks[user_id].append(walk_id)
    
    await callback.answer("✅ Вы записаны на прогулку!")
    
    current_members = len(walk["members"])
    max_members = int(walk["max"]) if walk["max"].isdigit() else 0
    members_text = f"{current_members}"
    if max_members > 0:
        members_text += f" / {max_members}"
    
    new_text = (
        f"📍 *{walk['name']}*\n"
        f"🗓 Когда: {walk['datetime']}\n"
        f"📍 Где: {walk['place']}\n"
        f"👥 Участников: {members_text}\n\n"
        f"✅ Вы идёте!"
    )
    if walk.get('description'):
        new_text += f"\n📝 {walk['description']}"
    
    await callback.message.edit_text(new_text, parse_mode="Markdown", reply_markup=None)

# --- Мои прогулки ---
@dp.message(lambda m: m.text == "👤 Мои прогулки")
async def my_walks(message: types.Message):
    user_id = message.from_user.id
    
    my_walks_list = []
    for walk in walks:
        if user_id in walk["members"] or walk["creator"] == user_id:
            my_walks_list.append(walk)
    
    if not my_walks_list:
        await message.answer("Вы пока не участвуете и не создали ни одной прогулки.")
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
            f"🗓 Когда: {walk['datetime']}\n"
            f"📍 Где: {walk['place']}\n"
            f"👥 Участников: {members_text}"
        )
        if walk.get('description'):
            full_text += f"\n📝 {walk['description']}"
        
        if not has_free_spots(walk) and walk["creator"] != user_id:
            full_text += "\n\n⚠️ Мест больше нет"
        
        if walk["creator"] == user_id:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Удалить прогулку", callback_data=f"delete_{walk['id']}")]
            ])
            await message.answer(full_text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(full_text, parse_mode="Markdown")

# --- Удалить прогулку ---
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
        await callback.answer("Прогулка не найдена!")
        return
    
    if walk_to_delete["creator"] != user_id:
        await callback.answer("Вы можете удалять только свои прогулки!")
        return
    
    walks[:] = [walk for walk in walks if walk["id"] != walk_id]
    
    for user in user_walks:
        if walk_id in user_walks[user]:
            user_walks[user].remove(walk_id)
    
    await callback.answer("Прогулка удалена!")
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ Прогулка удалена",
        reply_markup=None
    )

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

    
