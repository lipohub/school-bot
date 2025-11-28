
from telebot import types

def register_handlers(bot):
    @bot.message_handler(commands=['admin'])
    def admin_menu_handler(message):
        if message.from_user.id not in bot.config.ADMIN_IDS:
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

    @bot.callback_query_handler(func=lambda c: c.data == 'admin_add')
    def admin_add_start(call):
        msg = bot.send_message(call.message.chat.id, "Введи ФИО:")
        bot.register_next_step_handler(msg, admin_add_name)

    def admin_add_name(message):
        full_name = message.text.strip()
        if not full_name:
            bot.send_message(message.chat.id, "ФИО не может быть пустым. Попробуй заново.")
            msg = bot.send_message(message.chat.id, "Введи ФИО:")
            bot.register_next_step_handler(msg, admin_add_name)
            return
        msg = bot.send_message(message.chat.id, "Введи класс (10А):")
        bot.register_next_step_handler(msg, admin_add_class, full_name)

    def admin_add_class(message, full_name):
        class_name = message.text.strip()
        if not class_name:
            bot.send_message(message.chat.id, "Класс не может быть пустым. Попробуй заново.")
            msg = bot.send_message(message.chat.id, "Введи класс (10А):")
            bot.register_next_step_handler(msg, admin_add_class, full_name)
            return
        uid = bot.generate_key(full_name, class_name)
        if uid in bot.db:
            bot.send_message(message.chat.id, "Этот ученик уже существует. Используй редактирование.")
            return
        bot.db[uid] = {
            'full_name': full_name,
            'class': class_name,
            'opinions': []
        }
        msg = bot.send_message(message.chat.id, "Введи ДР (15.03.2008):")
        bot.register_next_step_handler(msg, admin_add_birthday, uid)

    def admin_add_birthday(message, uid):
        bot.db[uid]['birthday'] = message.text.strip()
        msg = bot.send_message(message.chat.id, "Введи телефон (или пусто):")
        bot.register_next_step_handler(msg, admin_add_phone, uid)

    def admin_add_phone(message, uid):
        bot.db[uid]['phone'] = message.text.strip()
        msg = bot.send_message(message.chat.id, "Введи Telegram (@username или пусто):")
        bot.register_next_step_handler(msg, admin_add_tg, uid)

    def admin_add_tg(message, uid):
        bot.db[uid]['tg'] = message.text.strip()
        msg = bot.send_message(message.chat.id, "Введи ВК (или пусто):")
        bot.register_next_step_handler(msg, admin_add_vk, uid)

    def admin_add_vk(message, uid):
        bot.db[uid]['vk'] = message.text.strip()
        msg = bot.send_message(message.chat.id, "Введи интересы (или пусто):")
        bot.register_next_step_handler(msg, admin_add_interests, uid)

    def admin_add_interests(message, uid):
        bot.db[uid]['interests'] = message.text.strip()
        msg = bot.send_message(message.chat.id, "Введи описание (до 500 симв., или пусто):")
        bot.register_next_step_handler(msg, admin_add_description, uid)

    def admin_add_description(message, uid):
        text = message.text.strip()
        if len(text) > 500:
            bot.send_message(message.chat.id, "Слишком длинно! Попробуй заново.")
            msg = bot.send_message(message.chat.id, "Введи описание (до 500 симв., или пусто):")
            bot.register_next_step_handler(msg, admin_add_description, uid)
            return
        bot.db[uid]['description'] = text
        bot.db[uid]['approved'] = True
        bot.save_db(bot.db)
        msg = bot.send_message(message.chat.id, "Прикрепи фото (или отправь 'нет'):")
        bot.register_next_step_handler(msg, admin_add_photo, uid)

    def admin_add_photo(message, uid):
        if message.text and message.text.lower() == 'нет':
            bot.send_message(message.chat.id, f"Добавлен {bot.db[uid]['full_name']}! Без фото.")
            return
        if message.photo:
            bot.db[uid]['photo_id'] = message.photo[-1].file_id
            bot.save_db(bot.db)
            bot.send_message(message.chat.id, f"Добавлен {bot.db[uid]['full_name']}! С фото.")
        else:
            bot.send_message(message.chat.id, "Отправь фото или 'нет'.")
            msg = bot.send_message(message.chat.id, "Прикрепи фото (или отправь 'нет'):")
            bot.register_next_step_handler(msg, admin_add_photo, uid)