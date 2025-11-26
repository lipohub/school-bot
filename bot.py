import telebot
import json
import os
from telebot import types
from datetime import datetime

BOT_TOKEN = '8483130885:AAEBgryQXbUnNUuS22ZJeUdQVOo4Jua6Vx0'
ADMIN_IDS = [1967855685]  # ← твои ID и ID других админов (список)

bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = 'students.json'

# Загружаем базу
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Сохраняем базу
def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_db()

# Проверка, является ли пользователь админом
def is_admin(user_id):
    return user_id in ADMIN_IDS

# === Главное меню для пользователей ===
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🔍 Найти ученика", callback_data="search"))
    kb.add(types.InlineKeyboardButton("➕ Дать наводку / добавить себя", callback_data="add_tip"))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        "Привет! Это поисковик учеников нашей школы\n\n"
        "Тут можно найти инфу о человеке или оставить заявку на добавление/исправление данных.",
        reply_markup=main_menu())

# === Поиск человека ===
@bot.callback_query_handler(func=lambda c: c.data == 'search')
def search_start(call):
    msg = bot.send_message(call.message.chat.id, "Напиши фамилию или имя ученика:")
    bot.register_next_step_handler(msg, process_search)

def process_search(message):
    query = message.text.lower()
    results = []
    for uid, data in db.items():
        if not data.get('approved', False):
            continue
        if query in data['full_name'].lower() or query in data.get('class', ''):
            results.append((uid, data))

    if not results:
        bot.send_message(message.chat.id, "Ничего не нашёл 😔", reply_markup=main_menu())
        return

    kb = types.InlineKeyboardMarkup(row_width=1)
    for uid, data in results[:20]:  # максимум 20 результатов
        kb.add(types.InlineKeyboardButton(
            f"{data['full_name']} • {data['class']}",
            callback_data=f"profile_{uid}"
        ))
    bot.send_message(message.chat.id, "Выбери человека:", reply_markup=kb)

# === Профиль человека ===
@bot.callback_query_handler(func=lambda c: c.data.startswith('profile_'))
def show_profile(call):
    uid = call.data.split('_')[1]
    data = db.get(uid, {})
    if not data.get('approved'):
        bot.answer_callback_query(call.id, "Информация ещё не проверена")
        return

    text = (f"*{data['full_name']}*\n"
            f"Класс: {data['class']}\n")
    
    if data.get('birthday'): text += f"ДР: {data['birthday']}\n"
    if data.get('phone'): text += f"Телефон: {data['phone']}\n"
    if data.get('tg'): text += f"Telegram: {data['tg']}\n"
    if data.get('vk'): text += f"ВК: {data['vk']}\n"
    if data.get('interests'): text += f"Интересы: {data['interests']}\n"
    if data.get('description'): text += f"\nОписание: {data['description']}\n"

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="search"))
    kb.add(types.InlineKeyboardButton("📝 Добавить мнение", callback_data=f"add_opinion_{uid}"))
    if data.get('opinions'):
        kb.add(types.InlineKeyboardButton("💬 Мнения ({len(data['opinions'])})", callback_data=f"view_opinions_{uid}_1"))

    if data.get('photo_id'):
        bot.send_photo(call.message.chat.id, data['photo_id'], caption=text, parse_mode='Markdown', reply_markup=kb)
    else:
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=kb)

# === Добавление/исправление данных от пользователей ===
@bot.callback_query_handler(func=lambda c: c.data == 'add_tip')
def add_tip_start(call):
    msg = bot.send_message(call.message.chat.id,
        "Напиши одним сообщением всё, что знаешь или хочешь исправить.\n"
        "Формат (пример):\n\n"
        "Иванов Иван\n10А\n15.03.2008\n+79991234567\n@ivanov_tg\nvk.com/ivanov2008\nфутбол, программирование\nОписание: Крутой парень, любит кодинг.")
    
    bot.register_next_step_handler(msg, process_tip, call.from_user.id)

def process_tip(message, user_id):
    tip_text = message.text.strip()
    
    bot.send_message(message.chat.id, 
        "Спасибо! Я отправил твою наводку админам на проверку.\n"
        "Как только проверят — информация появится в поиске.", 
        reply_markup=main_menu())

    # Пересылаем админам с данными отправителя
    info = f"Новая наводка от @{message.from_user.username} ({message.from_user.id})\n\n{tip_text}"
    for admin in ADMIN_IDS:
        bot.send_message(admin, info)

# === Добавление мнения ===
@bot.callback_query_handler(func=lambda c: c.data.startswith('add_opinion_'))
def add_opinion_start(call):
    uid = call.data.split('_')[2]
    msg = bot.send_message(call.message.chat.id, "Напиши своё мнение (до 200 символов):")
    bot.register_next_step_handler(msg, process_opinion, uid, call.from_user.id)

def process_opinion(message, uid, user_id):
    text = message.text.strip()
    if len(text) > 200:
        bot.send_message(message.chat.id, "Слишком длинно! Максимум 200 символов.")
        return

    bot.send_message(message.chat.id, "Спасибо! Мнение отправлено на проверку админам.")

    # Пересылаем админам с данными отправителя
    info = f"Новое мнение о {db[uid]['full_name']} от @{message.from_user.username} ({message.from_user.id})\n\n{text}"
    for admin in ADMIN_IDS:
        bot.send_message(admin, info)

# === Просмотр мнений с пагинацией ===
@bot.callback_query_handler(func=lambda c: c.data.startswith('view_opinions_'))
def view_opinions(call):
    parts = call.data.split('_')
    uid = parts[2]
    page = int(parts[3])
    data = db.get(uid, {})
    opinions = [op for op in data.get('opinions', []) if op.get('approved')]

    if not opinions:
        bot.answer_callback_query(call.id, "Нет мнений")
        return

    per_page = 10
    total_pages = (len(opinions) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    current_opinions = opinions[start:end]

    text = f"Мнения о {data['full_name']} (страница {page}/{total_pages}):\n\n"
    for idx, op in enumerate(current_opinions, start=start+1):
        text += f"{idx}. {op['text']} (@{op['author_username']}, {op['date']})\n\n"

    kb = types.InlineKeyboardMarkup(row_width=2)
    if page > 1:
        kb.add(types.InlineKeyboardButton("◀️ Предыдущая", callback_data=f"view_opinions_{uid}_{page-1}"))
    if page < total_pages:
        kb.add(types.InlineKeyboardButton("Следующая ▶️", callback_data=f"view_opinions_{uid}_{page+1}"))
    kb.add(types.InlineKeyboardButton("🔙 К профилю", callback_data=f"profile_{uid}"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

# === АДМИН-МЕНЮ ===
@bot.message_handler(commands=['admin'])
def admin_menu_handler(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Доступ запрещён.")
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Добавить", callback_data="admin_add"),
        types.InlineKeyboardButton("✏️ Редактировать", callback_data="admin_edit")
    )
    kb.add(
        types.InlineKeyboardButton("❌ Удалить", callback_data="admin_delete"),
        types.InlineKeyboardButton("📋 Список всех", callback_data="admin_list")
    )
    kb.add(types.InlineKeyboardButton("📤 Экспорт базы", callback_data="admin_export"))
    kb.add(types.InlineKeyboardButton("💬 Управление мнениями", callback_data="admin_opinions"))

    bot.send_message(message.chat.id, "Админ-меню:", reply_markup=kb)

# === Админ: Добавить ученика (с новыми полями) ===
@bot.callback_query_handler(func=lambda c: c.data == 'admin_add')
def admin_add_start(call):
    if not is_admin(call.from_user.id):
        return
    msg = bot.send_message(call.message.chat.id, "Введи Telegram ID ученика (число):")
    bot.register_next_step_handler(msg, admin_add_id)

def admin_add_id(message):
    try:
        uid = str(int(message.text.strip()))  # Преобразуем в строку для JSON
        if uid in db:
            bot.send_message(message.chat.id, "Этот ID уже есть в базе. Используй редактирование.")
            return
        db[uid] = {'opinions': []}  # Временный словарь с мнениями
        msg = bot.send_message(message.chat.id, "Введи ФИО (полное имя):")
        bot.register_next_step_handler(msg, admin_add_name, uid)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный ID. Должен быть числом.")

def admin_add_name(message, uid):
    db[uid]['full_name'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи класс (например, 10А):")
    bot.register_next_step_handler(msg, admin_add_class, uid)

def admin_add_class(message, uid):
    db[uid]['class'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи дату рождения (например, 15.03.2008):")
    bot.register_next_step_handler(msg, admin_add_birthday, uid)

def admin_add_birthday(message, uid):
    db[uid]['birthday'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи телефон (или пусто):")
    bot.register_next_step_handler(msg, admin_add_phone, uid)

def admin_add_phone(message, uid):
    db[uid]['phone'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи Telegram (@username или ссылку, или пусто):")
    bot.register_next_step_handler(msg, admin_add_tg, uid)

def admin_add_tg(message, uid):
    db[uid]['tg'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи ссылку на ВК (или пусто):")
    bot.register_next_step_handler(msg, admin_add_vk, uid)

def admin_add_vk(message, uid):
    db[uid]['vk'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи интересы (через запятую, или пусто):")
    bot.register_next_step_handler(msg, admin_add_interests, uid)

def admin_add_interests(message, uid):
    db[uid]['interests'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи описание (до 500 символов, или пусто):")
    bot.register_next_step_handler(msg, admin_add_description, uid)

def admin_add_description(message, uid):
    text = message.text.strip()
    if len(text) > 500:
        bot.send_message(message.chat.id, "Слишком длинно! Максимум 500 символов.")
        return
    db[uid]['description'] = text
    db[uid]['approved'] = True
    save_db(db)
    bot.send_message(message.chat.id, f"Ученик {db[uid]['full_name']} добавлен!")

# === Админ: Редактировать (с новыми полями) ===
@bot.callback_query_handler(func=lambda c: c.data == 'admin_edit')
def admin_edit_start(call):
    if not is_admin(call.from_user.id):
        return
    kb = get_students_kb("edit_select_")
    if not kb.keyboard:
        bot.send_message(call.message.chat.id, "База пуста.")
        return
    bot.send_message(call.message.chat.id, "Выбери ученика для редактирования:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('edit_select_'))
def admin_edit_select(call):
    uid = call.data.split('_')[2]
    kb = types.InlineKeyboardMarkup(row_width=2)
    fields = ['full_name', 'class', 'birthday', 'phone', 'tg', 'vk', 'interests', 'description']
    for field in fields:
        kb.add(types.InlineKeyboardButton(field.capitalize(), callback_data=f"edit_field_{uid}_{field}"))
    bot.edit_message_text(f"Выбери поле для редактирования у {db[uid]['full_name']}:", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('edit_field_'))
def admin_edit_field(call):
    parts = call.data.split('_')
    uid = parts[2]
    field = parts[3]
    msg = bot.send_message(call.message.chat.id, f"Введи новое значение для {field.capitalize()} (текущее: {db[uid].get(field, 'пусто')}):")
    bot.register_next_step_handler(msg, admin_edit_save, uid, field)

def admin_edit_save(message, uid, field):
    text = message.text.strip()
    if field == 'description' and len(text) > 500:
        bot.send_message(message.chat.id, "Слишком длинно! Максимум 500 символов.")
        return
    db[uid][field] = text
    save_db(db)
    bot.send_message(message.chat.id, f"Поле {field} обновлено для {db[uid]['full_name']}.")

# === Админ: Управление мнениями ===
@bot.callback_query_handler(func=lambda c: c.data == 'admin_opinions')
def admin_opinions_start(call):
    if not is_admin(call.from_user.id):
        return
    kb = get_students_kb("opinions_select_")
    if not kb.keyboard:
        bot.send_message(call.message.chat.id, "База пуста.")
        return
    bot.send_message(call.message.chat.id, "Выбери ученика для управления мнениями:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('opinions_select_'))
def admin_opinions_select(call):
    uid = call.data.split('_')[2]
    data = db.get(uid, {})
    opinions = data.get('opinions', [])
    text = f"Мнения о {data['full_name']} ({len(opinions)}):\n\n"
    for idx, op in enumerate(opinions):
        status = "✅" if op.get('approved') else "❌"
        text += f"{idx+1}. {op['text']} (@{op['author_username']}, {op['date']}) {status}\n\n"
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("➕ Добавить мнение вручную", callback_data=f"admin_add_opinion_{uid}"))
    kb.add(types.InlineKeyboardButton("✏️ Одобрить/отклонить", callback_data=f"admin_approve_opinions_{uid}"))
    kb.add(types.InlineKeyboardButton("❌ Удалить мнение", callback_data=f"admin_delete_opinion_{uid}"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

# Админ: Добавить мнение вручную
@bot.callback_query_handler(func=lambda c: c.data.startswith('admin_add_opinion_'))
def admin_add_opinion_start(call):
    uid = call.data.split('_')[3]
    msg = bot.send_message(call.message.chat.id, "Введи текст мнения (до 200 символов):")
    bot.register_next_step_handler(msg, admin_add_opinion_text, uid)

def admin_add_opinion_text(message, uid):
    text = message.text.strip()
    if len(text) > 200:
        bot.send_message(message.chat.id, "Слишком длинно! Максимум 200 символов.")
        return
    msg = bot.send_message(message.chat.id, "Введи author_id (ID отправителя):")
    bot.register_next_step_handler(msg, admin_add_opinion_author_id, uid, text)

def admin_add_opinion_author_id(message, uid, text):
    author_id = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи author_username (@username):")
    bot.register_next_step_handler(msg, admin_add_opinion_author_username, uid, text, author_id)

def admin_add_opinion_author_username(message, uid, text, author_id):
    author_username = message.text.strip()
    opinion = {
        'text': text,
        'author_id': author_id,
        'author_username': author_username,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'approved': True
    }
    db[uid]['opinions'].append(opinion)
    save_db(db)
    bot.send_message(message.chat.id, "Мнение добавлено и одобрено!")

# Админ: Одобрить/отклонить мнения (предполагаем, что админ вручную правит JSON или использует это для простоты)
@bot.callback_query_handler(func=lambda c: c.data.startswith('admin_approve_opinions_'))
def admin_approve_opinions(call):
    uid = call.data.split('_')[3]
    bot.send_message(call.message.chat.id, "Для одобрения/отклонения отредактируй JSON вручную или используй удаление. Это базовая версия.")

# Админ: Удалить мнение
@bot.callback_query_handler(func=lambda c: c.data.startswith('admin_delete_opinion_'))
def admin_delete_opinion_start(call):
    uid = call.data.split('_')[3]
    opinions = db[uid].get('opinions', [])
    if not opinions:
        bot.send_message(call.message.chat.id, "Нет мнений.")
        return

    kb = types.InlineKeyboardMarkup(row_width=1)
    for idx, op in enumerate(opinions):
        kb.add(types.InlineKeyboardButton(f"{idx+1}. {op['text'][:20]}...", callback_data=f"delete_opinion_{uid}_{idx}"))

    bot.send_message(call.message.chat.id, "Выбери мнение для удаления:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('delete_opinion_'))
def admin_delete_opinion_confirm(call):
    parts = call.data.split('_')
    uid = parts[2]
    idx = int(parts[3])
    del db[uid]['opinions'][idx]
    save_db(db)
    bot.edit_message_text("Мнение удалено.", call.message.chat.id, call.message.message_id)

# === Админ: Удалить ученика ===
@bot.callback_query_handler(func=lambda c: c.data == 'admin_delete')
def admin_delete_start(call):
    if not is_admin(call.from_user.id):
        return
    kb = get_students_kb("delete_confirm_")
    if not kb.keyboard:
        bot.send_message(call.message.chat.id, "База пуста.")
        return
    bot.send_message(call.message.chat.id, "Выбери ученика для удаления:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('delete_confirm_'))
def admin_delete_confirm(call):
    uid = call.data.split('_')[2]
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Да, удалить", callback_data=f"delete_yes_{uid}"),
        types.InlineKeyboardButton("Нет", callback_data="cancel")
    )
    bot.edit_message_text(f"Удалить {db[uid]['full_name']}?", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('delete_yes_'))
def admin_delete_yes(call):
    uid = call.data.split('_')[2]
    del db[uid]
    save_db(db)
    bot.edit_message_text("Удалено.", call.message.chat.id, call.message.message_id)

# === Админ: Список всех ===
@bot.callback_query_handler(func=lambda c: c.data == 'admin_list')
def admin_list(call):
    if not is_admin(call.from_user.id):
        return
    text = "Все ученики:\n\n"
    for uid, data in db.items():
        text += f"{data['full_name']} ({data['class']}) - ID: {uid}\n"
    bot.send_message(call.message.chat.id, text or "База пуста.")

# === Админ: Экспорт базы ===
@bot.callback_query_handler(func=lambda c: c.data == 'admin_export')
def admin_export(call):
    if not is_admin(call.from_user.id):
        return
    with open(DB_FILE, 'rb') as f:
        bot.send_document(call.message.chat.id, f)

# === Отмена ===
@bot.callback_query_handler(func=lambda c: c.data == 'cancel')
def cancel(call):
    bot.edit_message_text("Действие отменено.", call.message.chat.id, call.message.message_id)

# Вспомогательная функция: Клавиатура со списком учеников
def get_students_kb(prefix):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for uid, data in sorted(db.items(), key=lambda x: x[1]['full_name']):
        kb.add(types.InlineKeyboardButton(
            f"{data['full_name']} • {data['class']}",
            callback_data=f"{prefix}{uid}"
        ))
    return kb

# === Запуск ===
bot.infinity_polling()
