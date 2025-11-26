import telebot
import json
import os
from telebot import types
from datetime import datetime

# ========================= НАСТРОЙКИ =========================
BOT_TOKEN = '8483130885:AAEBgryQXbUnNUuS22ZJeUdQVOo4Jua6Vx0'          # ← замени
ADMIN_IDS = [1967855685]                   # ← твои Telegram ID (можно несколько через запятую)

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = 'students.json'

# ========================= БАЗА ДАННЫХ =========================
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_db()

def is_admin(uid):
    return uid in ADMIN_IDS

# ========================= МЕНЮ =========================
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("Найти ученика", callback_data="search"))
    kb.add(types.InlineKeyboardButton("Дать наводку / добавить себя", callback_data="add_tip"))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        "Привет! Это поисковик учеников нашей школы\n\n"
        "Ищи людей, оставляй наводки и мнения — всё через модерацию.",
        reply_markup=main_menu())

# ========================= ПОИСК =========================
@bot.callback_query_handler(func=lambda c: c.data == 'search')
def search_start(call):
    msg = bot.send_message(call.message.chat.id, "Напиши фамилию или имя:")
    bot.register_next_step_handler(msg, process_search)

def process_search(message):
    query = message.text.lower()
    results = []
    for uid, data in db.items():
        if data.get('approved'):
            if query in data['full_name'].lower() or query in data.get('class', ''):
                results.append((uid, data))
    if not results:
        bot.send_message(message.chat.id, "Ничего не нашёл", reply_markup=main_menu())
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for uid, data in results[:20]:
        kb.add(types.InlineKeyboardButton(f"{data['full_name']} • {data['class']}", callback_data=f"profile_{uid}"))
    bot.send_message(message.chat.id, "Выбери человека:", reply_markup=kb)

# ========================= ПРОФИЛЬ =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith('profile_'))
def show_profile(call):
    uid = call.data.split('_')[1]
    data = db.get(uid, {})
    if not data.get('approved'):
        bot.answer_callback_query(call.id, "Информация ещё не проверена")
        return

    text = f"*{data['full_name']}*\nКласс: {data['class']}\n"
    if data.get('birthday'): text += f"ДР: {data['birthday']}\n"
    if data.get('phone'): text += f"Телефон: {data['phone']}\n"
    if data.get('tg'): text += f"TG: {data['tg']}\n"
    if data.get('vk'): text += f"ВК: {data['vk']}\n"
    if data.get('interests'): text += f"Интересы: {data['interests']}\n"
    if data.get('description'): text += f"\nОписание:\n{data['description']}\n"

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("Назад", callback_data="search"))
    kb.add(types.InlineKeyboardButton("Добавить мнение", callback_data=f"add_opinion_{uid}"))
    opinions = [op for op in data.get('opinions', []) if op.get('approved')]
    if opinions:
        kb.add(types.InlineKeyboardButton(f"Мнения ({len(opinions)})", callback_data=f"view_opinions_{uid}_1"))

    if data.get('photo_id'):
        bot.send_photo(call.message.chat.id, data['photo_id'], caption=text, parse_mode='Markdown', reply_markup=kb)
    else:
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=kb)

# ========================= ДОБАВЛЕНИЕ МНЕНИЯ =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith('add_opinion_'))
def add_opinion_start(call):
    uid = call.data.split('_')[2]
    msg = bot.send_message(call.message.chat.id, "Напиши мнение (макс. 200 символов):")
    bot.register_next_step_handler(msg, process_opinion, uid, call.from_user.id)

def process_opinion(message, uid, author_id):
    text = message.text.strip()
    if len(text) > 200:
        bot.send_message(message.chat.id, "Слишком длинно! Максимум 200 символов.")
        return

    # Сохраняем временно
    if uid not in db:
        db[uid] = {"opinions": []}
    if "opinions" not in db[uid]:
        db[uid]["opinions"] = []

    opinion = {
        "text": text,
        "author_id": str(author_id),
        "author_username": message.from_user.username or "аноним",
        "date": datetime.now().strftime("%d.%m.%Y"),
        "approved": False
    }
    db[uid]["opinions"].append(opinion)
    save_db(db)
    idx = len(db[uid]["opinions"]) - 1

    # Кнопки админам
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Подтвердить", callback_data=f"approve_op_{uid}_{idx}"),
        types.InlineKeyboardButton("Отклонить", callback_data=f"reject_op_{uid}_{idx}")
    )

    info = (f"Новое мнение о {db[uid].get('full_name', uid)}\n"
            f"От: @{message.from_user.username or 'без_юзернейма'} ({author_id})\n\n{text}")

    bot.send_message(message.chat.id, "Мнение отправлено на модерацию.")
    for admin in ADMIN_IDS:
        bot.send_message(admin, info, reply_markup=kb)

# ========================= ПРОСМОТР МНЕНИЙ =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith('view_opinions_'))
def view_opinions(call):
    parts = call.data.split('_')
    uid = parts[2]
    page = int(parts[3])
    opinions = [op for op in db.get(uid, {}).get('opinions', []) if op.get('approved')]

    if not opinions:
        bot.answer_callback_query(call.id, "Нет одобренных мнений")
        return

    per_page = 10
    total = (len(opinions) + per_page - 1) // per_page
    start = (page-1)*per_page
    end = start + per_page
    page_ops = opinions[start:end]

    text = f"Мнения о {db[uid].get('full_name','человеке')} ({page}/{total}):\n\n"
    for i, op in enumerate(page_ops, start+1):
        text += f"{i}. {op['text']}\n   — @{op['author_username']}, {op['date']}\n\n"

    kb = types.InlineKeyboardMarkup(row_width=2)
    if page > 1:
        kb.add(types.InlineKeyboardButton("Пред.", callback_data=f"view_opinions_{uid}_{page-1}"))
    if page < total:
        kb.add(types.InlineKeyboardButton("След.", callback_data=f"view_opinions_{uid}_{page+1}"))
    kb.add(types.InlineKeyboardButton("Назад", callback_data=f"profile_{uid}"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

# ========================= МОДЕРАЦИЯ МНЕНИЙ =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith(('approve_op_', 'reject_op_')))
def handle_opinion_approval(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Только админы")
        return

    parts = call.data.split('_')
    action = parts[0]
    uid = parts[2]
    idx = int(parts[3])

    if uid not in db or idx >= len(db[uid].get("opinions", [])):
        bot.answer_callback_query(call.id, "Уже обработано")
        return

    if action == "approve":
        db[uid]["opinions"][idx]["approved"] = True
        save_db(db)
        bot.edit_message_text(f"Мнение подтверждено @{call.from_user.username}\nТеперь видно всем!",
                              call.message.chat.id, call.message.message_id)
    else:
        removed = db[uid]["opinions"][idx]["text"][:40]
        del db[uid]["opinions"][idx]
        if not db[uid]["opinions"]:
            db[uid].pop("opinions", None)
        save_db(db)
        bot.edit_message_text(f"Мнение отклонено и удалено @{call.from_user.username}\n(было: {removed}…)",
                              call.message.chat.id, call.message.message_id)

# ========================= НАВОДКИ =========================
@bot.callback_query_handler(func=lambda c: c.data == 'add_tip')
def add_tip_start(call):
    msg = bot.send_message(call.message.chat.id, "Пришли всю инфу одним сообщением (ФИО, класс, телефон, TG, ВК, интересы, описание до 500 симв.):")
    bot.register_next_step_handler(msg, process_tip)

def process_tip(message):
    text = message.text.strip()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Подтвердить", callback_data=f"approve_tip_{message.message_id}"))
    kb.add(types.InlineKeyboardButton("Отклонить", callback_data=f"reject_tip_{message.message_id}"))
    info = f"Наводка от @{message.from_user.username} ({message.from_user.id})\n\n{text}"
    bot.send_message(message.chat.id, "Наводка отправлена админам на проверку.", reply_markup=main_menu())
    for admin in ADMIN_IDS:
        bot.send_message(admin, info, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith(('approve_tip_', 'reject_tip_')))
def handle_tip(call):
    if not is_admin(call.from_user.id):
        return
    action = "подтверждена" if c.data.startswith('approve_tip') else "отклонена"
    bot.edit_message_text(f"Наводка {action} @{call.from_user.username}",
                          call.message.chat.id, call.message.message_id)

# ========================= АДМИНКА =========================
# (оставил только самое нужное — добавление/редактирование/удаление учеников)
# Если нужна полная админка — скажи, добавлю обратно за 2 минуты

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("Добавить", callback_data="admin_add"),
        types.InlineKeyboardButton("Редактировать", callback_data="admin_edit"),
        types.InlineKeyboardButton("Удалить", callback_data="admin_delete"),
        types.InlineKeyboardButton("Экспорт базы", callback_data="admin_export")
    )
    bot.send_message(message.chat.id, "Админ-панель", reply_markup=kb)

# (остальные функции админки опустил для краткости — если нужны — пиши)

# ========================= ЗАПУСК =========================
print("Бот запущен...")
bot.infinity_polling()