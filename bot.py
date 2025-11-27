import telebot
import json
import os
from telebot import types
from datetime import datetime
import hashlib  # Для генерации уникальных ключей, если нужно
import base64   # Для кодирования query в пагинации поиска

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

# Функция для генерации уникального ключа на основе full_name и class
def generate_key(full_name, class_name):
    hash_input = f"{full_name.lower()}_{class_name.lower()}"
    return hashlib.md5(hash_input.encode()).hexdigest()

# ========================= ГЛАВНОЕ МЕНЮ =========================
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🔍 Найти ученика", callback_data="search"))
    kb.add(types.InlineKeyboardButton("➕ Дать наводку / добавить себя", callback_data="add_tip"))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        "Привет! Это поисковик учеников нашей школы\n\n"
        "Тут можно найти инфу о человеке или оставить заявку на добавление/исправление данных.\n\n"
        "Доступные команды:\n"
        "/start - Главное меню\n"
        "/search - Поиск ученика\n"
        "/add_tip - Дать наводку\n"
        "/admin - Админ-панель (только для админов)\n"
        "/help - Список команд",
        reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id,
        "Доступные команды:\n"
        "/start - Главное меню\n"
        "/search - Поиск ученика\n"
        "/add_tip - Дать наводку\n"
        "/admin - Админ-панель (только для админов)\n"
        "/help - Этот список")

# ========================= ПОИСК =========================
@bot.message_handler(commands=['search'])
def search_command(message):
    msg = bot.send_message(message.chat.id, "Напиши фамилию или имя ученика:")
    bot.register_next_step_handler(msg, process_search)

@bot.callback_query_handler(func=lambda c: c.data == 'search')
def search_start(call):
    msg = bot.send_message(call.message.chat.id, "Напиши фамилию или имя ученика:")
    bot.register_next_step_handler(msg, process_search)

def process_search(message):
    query = message.text.lower().strip()
    if not query:
        bot.send_message(message.chat.id, "Запрос пустой 😔", reply_markup=main_menu())
        return

    results = []
    for uid, data in db.items():
        if not data.get('approved', False):
            continue
        if query in data['full_name'].lower() or query in data.get('class', '').lower():
            results.append((uid, data))

    if not results:
        bot.send_message(message.chat.id, "Ничего не нашёл 😔", reply_markup=main_menu())
        return

    results = sorted(results, key=lambda x: x[1]['full_name'])

    per_page = 10
    total_pages = (len(results) + per_page - 1) // per_page

    show_search_page(message.chat.id, query, 1, results, total_pages, message_id=None)

def show_search_page(chat_id, query, page, results, total_pages, message_id=None):
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    current_results = results[start:end]

    kb = types.InlineKeyboardMarkup(row_width=1)
    for uid, data in current_results:
        kb.add(types.InlineKeyboardButton(
            f"{data['full_name']} • {data['class']}",
            callback_data=f"profile_{uid}"
        ))

    row = []
    encoded_query = base64.b64encode(query.encode()).decode('utf-8')
    if page > 1:
        row.append(types.InlineKeyboardButton("◀️ Prev", callback_data=f"search_page_{encoded_query}_{page-1}"))
    if page < total_pages:
        row.append(types.InlineKeyboardButton("Next ▶️", callback_data=f"search_page_{encoded_query}_{page+1}"))
    if row:
        kb.row(*row)

    text = f"Выбери человека для '{query}' (страница {page}/{total_pages}):"

    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
    else:
        bot.send_message(chat_id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('search_page_'))
def handle_search_page(call):
    parts = call.data.split('_')
    encoded_query = parts[2]
    page = int(parts[3])
    query = base64.b64decode(encoded_query).decode('utf-8')

    results = []
    for uid, data in db.items():
        if not data.get('approved', False):
            continue
        if query in data['full_name'].lower() or query in data.get('class', '').lower():
            results.append((uid, data))

    results = sorted(results, key=lambda x: x[1]['full_name'])

    total_pages = (len(results) + 10 - 1) // 10

    if page < 1 or page > total_pages:
        bot.answer_callback_query(call.id, "Неверная страница")
        return

    show_search_page(call.message.chat.id, query, page, results, total_pages, call.message.message_id)

# ========================= ПРОФИЛЬ =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith('profile_'))
def show_profile(call):
    uid = call.data.split('_')[1]

    # Перезагружаем базу, чтобы видеть свежие изменения (мнения и т.д.)
    global db
    db = load_db()
    data = db.get(uid, {})
    if not data or not data.get('approved'):
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
    opinions = [op for op in data.get('opinions', []) if op.get('approved')]
    if opinions:
        kb.add(types.InlineKeyboardButton(f"💬 Мнения ({len(opinions)})", callback_data=f"view_opinions_{uid}_1"))

    if data.get('photo_id'):
        bot.send_photo(call.message.chat.id, data['photo_id'], caption=text, parse_mode='Markdown', reply_markup=kb)
    else:
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=kb)

# ========================= НАВОДКИ =========================
@bot.message_handler(commands=['add_tip'])
def add_tip_command(message):
    msg = bot.send_message(message.chat.id,
        "Напиши одним сообщением всё, что знаешь или хочешь исправить.\n"
        "Формат (пример):\n\n"
        "Иванов Иван\n10А\n15.03.2008\n+79991234567\n@ivanov_tg\nvk.com/ivanov2008\nфутбол, программирование\nОписание: Крутой парень, любит кодинг.\n\n"
        "Можешь прикрепить фото.")
    
    bot.register_next_step_handler(msg, process_tip, message.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == 'add_tip')
def add_tip_start(call):
    msg = bot.send_message(call.message.chat.id,
        "Напиши одним сообщением всё, что знаешь или хочешь исправить.\n"
        "Формат (пример):\n\n"
        "Иванов Иван\n10А\n15.03.2008\n+79991234567\n@ivanov_tg\nvk.com/ivanov2008\nфутбол, программирование\nОписание: Крутой парень, любит кодинг.\n\n"
        "Можешь прикрепить фото.")
    
    bot.register_next_step_handler(msg, process_tip, call.from_user.id)

def process_tip(message, user_id):
    tip_text = message.text.strip() if message.text else ""
    photo_id = message.photo[-1].file_id if message.photo else None
    
    bot.send_message(message.chat.id, 
        "Спасибо! Я отправил твою наводку админам на проверку.\n"
        "Как только проверят — информация появится в поиске.", 
        reply_markup=main_menu())

    # Формируем сообщение админам с кнопками
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Подтвердить наводку", callback_data=f"approve_tip_{message.message_id}"),
        types.InlineKeyboardButton("Отклонить", callback_data=f"reject_tip_{message.message_id}")
    )
    
    info = (f"Новая наводка от @{message.from_user.username} ({message.from_user.id})\n"
            f"Сообщение ID: {message.message_id}\n\n{tip_text}")
    
    for admin in ADMIN_IDS:
        if photo_id:
            bot.send_photo(admin, photo_id, caption=info, reply_markup=kb)
        else:
            bot.send_message(admin, info, reply_markup=kb)

def parse_tip(tip_text):
    lines = tip_text.split('\n')
    if len(lines) < 2:
        return None
    data = {
        'full_name': lines[0].strip(),
        'class': lines[1].strip(),
        'birthday': lines[2].strip() if len(lines) > 2 else '',
        'phone': lines[3].strip() if len(lines) > 3 else '',
        'tg': lines[4].strip() if len(lines) > 4 else '',
        'vk': lines[5].strip() if len(lines) > 5 else '',
        'interests': lines[6].strip() if len(lines) > 6 else '',
        'description': '\n'.join(lines[7:]).strip() if len(lines) > 7 else ''
    }
    # Базовая валидация
    if not data['full_name'] or not data['class']:
        return None
    return data

@bot.callback_query_handler(func=lambda c: c.data.startswith('approve_tip_') or c.data.startswith('reject_tip_'))
def handle_tip_approval(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Ты не админ")
        return
    
    is_approve = call.data.startswith('approve_tip_')
    action = "подтверждена" if is_approve else "отклонена"
    
    # Извлекаем tip_text из сообщения
    message_text = call.message.text or call.message.caption
    parts = message_text.split('\n\n')
    tip_text = parts[1] if len(parts) > 1 else ""
    
    # Фото, если есть
    photo_id = call.message.photo[-1].file_id if call.message.photo else None
    
    if is_approve:
        parsed_data = parse_tip(tip_text)
        if not parsed_data:
            bot.edit_message_text("Ошибка парсинга наводки. Добавьте вручную.", 
                                  call.message.chat.id, call.message.message_id)
            return
        
        # Ищем существующий профиль по full_name и class
        existing_uid = None
        for uid, data in db.items():
            if data.get('full_name', '').lower() == parsed_data['full_name'].lower() and data.get('class', '').lower() == parsed_data['class'].lower():
                existing_uid = uid
                break
        
        if existing_uid:
            # Обновляем существующий
            db[existing_uid].update(parsed_data)
            uid = existing_uid
        else:
            # Создаем новый с генерированным ключом
            uid = generate_key(parsed_data['full_name'], parsed_data['class'])
            db[uid] = parsed_data
        
        db[uid]['approved'] = True
        if photo_id:
            db[uid]['photo_id'] = photo_id
        if 'opinions' not in db[uid]:
            db[uid]['opinions'] = []
        save_db(db)
        
        bot.edit_message_text(f"Наводка {action} админом @{call.from_user.username}. Профиль {'обновлен' if existing_uid else 'добавлен'}.", 
                              call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text(f"Наводка {action} админом @{call.from_user.username}", 
                              call.message.chat.id, call.message.message_id)

# ========================= ДОБАВЛЕНИЕ МНЕНИЯ =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith('add_opinion_'))
def add_opinion_start(call):
    uid = call.data.split('_')[2]
    if uid not in db:
        bot.answer_callback_query(call.id, "Профиль не найден")
        return
    msg = bot.send_message(call.message.chat.id, "Напиши своё мнение (до 200 символов):")
    bot.register_next_step_handler(msg, process_opinion, uid, call.from_user.id)

def process_opinion(message, uid, user_id):
    text = message.text.strip()
    if len(text) > 200:
        bot.send_message(message.chat.id, "Слишком длинно! Максимум 200 символов.")
        msg = bot.send_message(message.chat.id, "Напиши своё мнение заново (до 200 символов):")
        bot.register_next_step_handler(msg, process_opinion, uid, user_id)
        return

    bot.send_message(message.chat.id, "Спасибо! Мнение отправлено на проверку админам.")

    # Сохраняем временно в базе с approved=False
    if "opinions" not in db[uid]:
        db[uid]["opinions"] = []

    opinion = {
        "text": text,
        "author_id": str(message.from_user.id),
        "author_username": message.from_user.username or 'без_юзернейма',
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "approved": False
    }
    db[uid]["opinions"].append(opinion)
    save_db(db)
    idx = len(db[uid]["opinions"]) - 1

    # Сообщение админам с кнопками
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Подтвердить", callback_data=f"approve_op_{uid}_{idx}"),
        types.InlineKeyboardButton("Отклонить", callback_data=f"reject_op_{uid}_{idx}")
    )
    
    info = (f"Новое мнение о {db[uid].get('full_name', 'ID '+uid)}\n"
            f"От: @{message.from_user.username} ({message.from_user.id})\n\n{text}")
    
    for admin in ADMIN_IDS:
        bot.send_message(admin, info, reply_markup=kb)

# ========================= ПРОСМОТР МНЕНИЙ =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith('view_opinions_'))
def view_opinions(call):
    parts = call.data.split('_')
    uid = parts[2]
    page = int(parts[3])

    # Перезагружаем базу, чтобы видеть свежие изменения
    global db
    db = load_db()
    data = db.get(uid, {})
    if not data:
        bot.answer_callback_query(call.id, "Профиль не найден")
        return
    opinions = [op for op in data.get('opinions', []) if op.get('approved', False)]

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

# ========================= МОДЕРАЦИЯ МНЕНИЙ =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith('approve_op_') or c.data.startswith('reject_op_'))
def handle_opinion_approval(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Ты не админ")
        return

    parts = call.data.split('_')
    action = parts[0]
    uid = parts[2]
    index = int(parts[3])

    if uid not in db or index >= len(db[uid].get("opinions", [])):
        bot.answer_callback_query(call.id, "Мнение не найдено")
        return

    if action == 'approve':
        db[uid]["opinions"][index]["approved"] = True
        save_db(db)
        bot.edit_message_text(f"Мнение подтверждено админом @{call.from_user.username}\nТеперь видно всем!", 
                              call.message.chat.id, call.message.message_id)
    else:
        del db[uid]["opinions"][index]
        if not db[uid]["opinions"]:
            del db[uid]["opinions"]
        save_db(db)
        bot.edit_message_text(f"Мнение отклонено админом @{call.from_user.username}", 
                              call.message.chat.id, call.message.message_id)

# ========================= АДМИН-ПАНЕЛЬ =========================
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

# ========================= АДМИН: СПИСОК ВСЕХ =========================
@bot.callback_query_handler(func=lambda c: c.data == 'admin_list')
def admin_list(call):
    if not is_admin(call.from_user.id):
        return

    # Перезагружаем базу
    global db
    db = load_db()

    students = sorted(db.items(), key=lambda x: x[1].get('full_name', ''))

    if not students:
        bot.send_message(call.message.chat.id, "База пуста.")
        return

    per_page = 20  # Больше, так как текст короткий
    total_pages = (len(students) + per_page - 1) // per_page

    show_admin_list_page(call.message.chat.id, 1, students, total_pages, message_id=None)

def show_admin_list_page(chat_id, page, students, total_pages, message_id=None):
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page
    current_students = students[start:end]

    text = f"Все ученики (страница {page}/{total_pages}):\n\n"
    for uid, data in current_students:
        approved = "✅" if data.get('approved', False) else "❌"
        text += f"{data.get('full_name', 'Без имени')} ({data.get('class', 'Без класса')}) - ID: {uid} {approved}\n"

    kb = types.InlineKeyboardMarkup(row_width=2)
    if page > 1:
        kb.add(types.InlineKeyboardButton("◀️ Prev", callback_data=f"admin_list_page_{page-1}"))
    if page < total_pages:
        kb.add(types.InlineKeyboardButton("Next ▶️", callback_data=f"admin_list_page_{page+1}"))

    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
    else:
        bot.send_message(chat_id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('admin_list_page_'))
def handle_admin_list_page(call):
    if not is_admin(call.from_user.id):
        return

    parts = call.data.split('_')
    page = int(parts[3])

    # Перезагружаем базу
    global db
    db = load_db()

    students = sorted(db.items(), key=lambda x: x[1].get('full_name', ''))

    total_pages = (len(students) + 20 - 1) // 20

    if page < 1 or page > total_pages:
        bot.answer_callback_query(call.id, "Неверная страница")
        return

    show_admin_list_page(call.message.chat.id, page, students, total_pages, call.message.message_id)

# ========================= АДМИН: ДОБАВИТЬ УЧЕНИКА =========================
@bot.callback_query_handler(func=lambda c: c.data == 'admin_add')
def admin_add_start(call):
    if not is_admin(call.from_user.id):
        return
    msg = bot.send_message(call.message.chat.id, "Введи ФИО:")
    bot.register_next_step_handler(msg, admin_add_name)

def admin_add_name(message):
    full_name = message.text.strip()
    if not full_name:
        bot.send_message(message.chat.id, "ФИО не может быть пустым. Попробуй заново.")
        msg = bot.send_message(message.chat.id, "Введи ФИО:")
        bot.register_next_step_handler(msg, admin_add_name)
        return
    msg = bot.send_message(message.chat.id, "Введи класс:")
    bot.register_next_step_handler(msg, admin_add_class, full_name)

def admin_add_class(message, full_name):
    class_name = message.text.strip()
    if not class_name:
        bot.send_message(message.chat.id, "Класс не может быть пустым. Попробуй заново.")
        msg = bot.send_message(message.chat.id, "Введи класс:")
        bot.register_next_step_handler(msg, admin_add_class, full_name)
        return
    uid = generate_key(full_name, class_name)
    if uid in db:
        bot.send_message(message.chat.id, "Этот ученик уже существует. Используй редактирование.")
        return
    db[uid] = {
        'full_name': full_name,
        'class': class_name,
        'opinions': []
    }
    msg = bot.send_message(message.chat.id, "Введи ДР:")
    bot.register_next_step_handler(msg, admin_add_birthday, uid)

def admin_add_birthday(message, uid):
    db[uid]['birthday'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи телефон (или пусто):")
    bot.register_next_step_handler(msg, admin_add_phone, uid)

def admin_add_phone(message, uid):
    db[uid]['phone'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи Telegram (@username или пусто):")
    bot.register_next_step_handler(msg, admin_add_tg, uid)

def admin_add_tg(message, uid):
    db[uid]['tg'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи ВК (или пусто):")
    bot.register_next_step_handler(msg, admin_add_vk, uid)

def admin_add_vk(message, uid):
    db[uid]['vk'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи интересы (или пусто):")
    bot.register_next_step_handler(msg, admin_add_interests, uid)

def admin_add_interests(message, uid):
    db[uid]['interests'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введи описание (до 500 симв., или пусто):")
    bot.register_next_step_handler(msg, admin_add_description, uid)

def admin_add_description(message, uid):
    text = message.text.strip()
    if len(text) > 500:
        bot.send_message(message.chat.id, "Слишком длинно! Попробуй заново.")
        msg = bot.send_message(message.chat.id, "Введи описание (до 500 симв., или пусто):")
        bot.register_next_step_handler(msg, admin_add_description, uid)
        return
    db[uid]['description'] = text
    db[uid]['approved'] = True
    save_db(db)
    msg = bot.send_message(message.chat.id, "Прикрепи фото (или отправь 'нет'):")
    bot.register_next_step_handler(msg, admin_add_photo, uid)

def admin_add_photo(message, uid):
    if message.text and message.text.lower() == 'нет':
        bot.send_message(message.chat.id, f"Добавлен {db[uid]['full_name']}! Без фото.")
        return
    if message.photo:
        db[uid]['photo_id'] = message.photo[-1].file_id
        save_db(db)
        bot.send_message(message.chat.id, f"Добавлен {db[uid]['full_name']}! С фото.")
    else:
        bot.send_message(message.chat.id, "Отправь фото или 'нет'.")
        msg = bot.send_message(message.chat.id, "Прикрепи фото (или отправь 'нет'):")
        bot.register_next_step_handler(msg, admin_add_photo, uid)

# ========================= АДМИН: РЕДАКТИРОВАТЬ =========================
@bot.callback_query_handler(func=lambda c: c.data == 'admin_edit')
def admin_edit_start(call):
    if not is_admin(call.from_user.id):
        return
    kb = get_students_kb("edit_select_")
    if not kb.keyboard:
        bot.send_message(call.message.chat.id, "База пуста.")
        return
    bot.send_message(call.message.chat.id, "Выбери для редактирования:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('edit_select_'))
def admin_edit_select(call):
    uid = call.data.split('_')[2]
    kb = types.InlineKeyboardMarkup(row_width=2)
    fields = ['full_name', 'class', 'birthday', 'phone', 'tg', 'vk', 'interests', 'description', 'photo_id']
    for field in fields:
        kb.add(types.InlineKeyboardButton(field.capitalize(), callback_data=f"edit_field_{uid}_{field}"))
    bot.edit_message_text(f"Поле для редактирования у {db[uid]['full_name']}:", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('edit_field_'))
def admin_edit_field(call):
    parts = call.data.split('_')
    uid = parts[2]
    field = parts[3]
    if field == 'photo_id':
        msg = bot.send_message(call.message.chat.id, "Прикрепи новое фото (или 'нет' для удаления):")
        bot.register_next_step_handler(msg, admin_edit_photo, uid)
    else:
        msg = bot.send_message(call.message.chat.id, f"Новое значение для {field} (текущее: {db[uid].get(field, 'пусто')}):")
        bot.register_next_step_handler(msg, admin_edit_save, uid, field)

def admin_edit_save(message, uid, field):
    text = message.text.strip()
    if field == 'description' and len(text) > 500:
        bot.send_message(message.chat.id, "Слишком длинно! Попробуй заново.")
        msg = bot.send_message(message.chat.id, f"Новое значение для {field} (текущее: {db[uid].get(field, 'пусто')}):")
        bot.register_next_step_handler(msg, admin_edit_save, uid, field)
        return
    if (field == 'full_name' or field == 'class') and not text:
        bot.send_message(message.chat.id, f"{field.capitalize()} не может быть пустым. Попробуй заново.")
        msg = bot.send_message(message.chat.id, f"Новое значение для {field} (текущее: {db[uid].get(field, 'пусто')}):")
        bot.register_next_step_handler(msg, admin_edit_save, uid, field)
        return
    # Если меняем full_name или class, нужно проверить на дубликат с новым ключом
    if field in ['full_name', 'class']:
        new_full_name = text if field == 'full_name' else db[uid]['full_name']
        new_class = text if field == 'class' else db[uid]['class']
        new_uid = generate_key(new_full_name, new_class)
        if new_uid != uid and new_uid in db:
            bot.send_message(message.chat.id, "Ученик с таким ФИО и классом уже существует.")
            return
        # Если ок, обновляем и меняем ключ если нужно
        db[new_uid] = db.pop(uid)
        uid = new_uid
    db[uid][field] = text
    save_db(db)
    bot.send_message(message.chat.id, f"Обновлено {field} для {db[uid]['full_name']}.")

def admin_edit_photo(message, uid):
    if message.text and message.text.lower() == 'нет':
        if 'photo_id' in db[uid]:
            del db[uid]['photo_id']
        save_db(db)
        bot.send_message(message.chat.id, "Фото удалено.")
        return
    if message.photo:
        db[uid]['photo_id'] = message.photo[-1].file_id
        save_db(db)
        bot.send_message(message.chat.id, "Фото обновлено.")
    else:
        bot.send_message(message.chat.id, "Отправь фото или 'нет'.")
        msg = bot.send_message(message.chat.id, "Прикрепи новое фото (или 'нет' для удаления):")
        bot.register_next_step_handler(msg, admin_edit_photo, uid)

# ========================= АДМИН: УДАЛИТЬ =========================
@bot.callback_query_handler(func=lambda c: c.data == 'admin_delete')
def admin_delete_start(call):
    if not is_admin(call.from_user.id):
        return
    kb = get_students_kb("delete_confirm_")
    if not kb.keyboard:
        bot.send_message(call.message.chat.id, "База пуста.")
        return
    bot.send_message(call.message.chat.id, "Выбери для удаления:", reply_markup=kb)

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

# ========================= АДМИН: ЭКСПОРТ БАЗЫ =========================
@bot.callback_query_handler(func=lambda c: c.data == 'admin_export')
def admin_export(call):
    if not is_admin(call.from_user.id):
        return
    with open(DB_FILE, 'rb') as f:
        bot.send_document(call.message.chat.id, f)

# ========================= АДМИН: УПРАВЛЕНИЕ МНЕНИЯМИ =========================
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
    kb.add(types.InlineKeyboardButton("❌ Удалить мнение", callback_data=f"admin_delete_opinion_{uid}"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

# АДМИН: ДОБАВИТЬ МНЕНИЕ ВРУЧНУЮ
@bot.callback_query_handler(func=lambda c: c.data.startswith('admin_add_opinion_'))
def admin_add_opinion_start(call):
    uid = call.data.split('_')[3]
    msg = bot.send_message(call.message.chat.id, "Введи текст мнения (до 200 симв.):")
    bot.register_next_step_handler(msg, admin_add_opinion_text, uid)

def admin_add_opinion_text(message, uid):
    text = message.text.strip()
    if len(text) > 200:
        bot.send_message(message.chat.id, "Слишком длинно! Попробуй заново.")
        msg = bot.send_message(message.chat.id, "Введи текст мнения (до 200 симв.):")
        bot.register_next_step_handler(msg, admin_add_opinion_text, uid)
        return
    msg = bot.send_message(message.chat.id, "Введи ID автора:")
    bot.register_next_step_handler(msg, admin_add_opinion_author_id, uid, text)

def admin_add_opinion_author_id(message, uid, text):
    author_id = message.text.strip()
    if not author_id.isdigit():
        bot.send_message(message.chat.id, "ID должен быть числом. Попробуй заново.")
        msg = bot.send_message(message.chat.id, "Введи ID автора:")
        bot.register_next_step_handler(msg, admin_add_opinion_author_id, uid, text)
        return
    msg = bot.send_message(message.chat.id, "Введи username автора (@username):")
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
    if 'opinions' not in db[uid]:
        db[uid]['opinions'] = []
    db[uid]['opinions'].append(opinion)
    save_db(db)
    bot.send_message(message.chat.id, "Мнение добавлено и одобрено!")

# АДМИН: УДАЛИТЬ МНЕНИЕ
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
    if not db[uid]['opinions']:
        del db[uid]['opinions']
    save_db(db)
    bot.edit_message_text("Мнение удалено.", call.message.chat.id, call.message.message_id)

# ========================= ОТМЕНА =========================
@bot.callback_query_handler(func=lambda c: c.data == 'cancel')
def cancel(call):
    bot.edit_message_text("Действие отменено.", call.message.chat.id, call.message.message_id)

# ========================= СПИСОК УЧЕНИКОВ ДЛЯ КЛАВИАТУРЫ =========================
def get_students_kb(prefix):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for uid, data in sorted(db.items(), key=lambda x: x[1]['full_name']):
        if data.get('approved', False):  # Показываем только approved
            kb.add(types.InlineKeyboardButton(
                f"{data['full_name']} • {data['class']}",
                callback_data=f"{prefix}{uid}"
            ))
    return kb

# ========================= ЗАПУСК =========================
if __name__ == '__main__':
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Error: {e}")