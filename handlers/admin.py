# handlers/admin.py
from telebot import types
from utils import get_students_kb

def register_handlers(bot):
    @bot.message_handler(commands=['admin'])
    def admin_menu(message):
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
            bot.send_message(message.chat.id, f"Добавлен {bot.db[uid]['full_name']} ! Без фото.")
            return
        if message.photo:
            bot.db[uid]['photo_id'] = message.photo[-1].file_id
            bot.save_db(bot.db)
            bot.send_message(message.chat.id, f"Добавлен {bot.db[uid]['full_name']} ! С фото.")
        else:
            bot.send_message(message.chat.id, "Отправь фото или 'нет'.")
            msg = bot.send_message(message.chat.id, "Прикрепи фото (или отправь 'нет'):")
            bot.register_next_step_handler(msg, admin_add_photo, uid)

    @bot.callback_query_handler(func=lambda c: c.data == 'admin_edit')
    def admin_edit_start(call):
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
        bot.edit_message_text(f"Поле для редактирования у {bot.db[uid]['full_name']}:", call.message.chat.id, call.message.message_id, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('edit_field_'))
    def admin_edit_field(call):
        parts = call.data.split('_')
        uid = parts[2]
        field = parts[3]
        if field == 'photo_id':
            msg = bot.send_message(call.message.chat.id, "Прикрепи новое фото (или 'нет' для удаления):")
            bot.register_next_step_handler(msg, admin_edit_photo, uid)
        else:
            msg = bot.send_message(call.message.chat.id, f"Новое значение для {field} (текущее: {bot.db[uid].get(field, 'пусто')}):")
            bot.register_next_step_handler(msg, admin_edit_save, uid, field)

    def admin_edit_save(message, uid, field):
        text = message.text.strip()
        if field == 'description' and len(text) > 500:
            bot.send_message(message.chat.id, "Слишком длинно! Попробуй заново.")
            msg = bot.send_message(message.chat.id, f"Новое значение для {field} (текущее: {bot.db[uid].get(field, 'пусто')}):")
            bot.register_next_step_handler(msg, admin_edit_save, uid, field)
            return
        if (field == 'full_name' or field == 'class') and not text:
            bot.send_message(message.chat.id, f"{field.capitalize()} не может быть пустым. Попробуй заново.")
            msg = bot.send_message(message.chat.id, f"Новое значение для {field} (текущее: {bot.db[uid].get(field, 'пусто')}):")
            bot.register_next_step_handler(msg, admin_edit_save, uid, field)
            return
        # Если меняем full_name или class, нужно проверить на дубликат с новым ключом
        if field in ['full_name', 'class']:
            new_full_name = text if field == 'full_name' else bot.db[uid]['full_name']
            new_class = text if field == 'class' else bot.db[uid]['class']
            new_uid = bot.generate_key(new_full_name, new_class)
            if new_uid != uid and new_uid in bot.db:
                bot.send_message(message.chat.id, "Ученик с таким ФИО и классом уже существует.")
                return
            # Если ок, обновляем и меняем ключ если нужно
            bot.db[new_uid] = bot.db.pop(uid)
            uid = new_uid
        bot.db[uid][field] = text
        bot.save_db(bot.db)
        bot.send_message(message.chat.id, f"Обновлено {field} для {bot.db[uid]['full_name']}.")

    def admin_edit_photo(message, uid):
        if message.text and message.text.lower() == 'нет':
            if 'photo_id' in bot.db[uid]:
                del bot.db[uid]['photo_id']
            bot.save_db(bot.db)
            bot.send_message(message.chat.id, "Фото удалено.")
            return
        if message.photo:
            bot.db[uid]['photo_id'] = message.photo[-1].file_id
            bot.save_db(bot.db)
            bot.send_message(message.chat.id, "Фото обновлено.")
        else:
            bot.send_message(message.chat.id, "Отправь фото или 'нет'.")
            msg = bot.send_message(message.chat.id, "Прикрепи новое фото (или 'нет' для удаления):")
            bot.register_next_step_handler(msg, admin_edit_photo, uid)

    @bot.callback_query_handler(func=lambda c: c.data == 'admin_delete')
    def admin_delete_start(call):
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
        bot.edit_message_text(f"Удалить {bot.db[uid]['full_name']}?", call.message.chat.id, call.message.message_id, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('delete_yes_'))
    def admin_delete_yes(call):
        uid = call.data.split('_')[2]
        del bot.db[uid]
        bot.save_db(bot.db)
        bot.edit_message_text("Удалено.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data == 'admin_export')
    def admin_export(call):
        if call.from_user.id not in bot.config.ADMIN_IDS:
            return
        data = json.dumps(bot.db, ensure_ascii=False, indent=2).encode('utf-8')
        bot.send_document(call.message.chat.id, types.InputFile(data, filename="students.json"))

    @bot.callback_query_handler(func=lambda c: c.data == 'admin_opinions')
    def admin_opinions_start(call):
        kb = get_students_kb("opinions_select_")
        if not kb.keyboard:
            bot.send_message(call.message.chat.id, "База пуста.")
            return
        bot.send_message(call.message.chat.id, "Выбери ученика для управления мнениями:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('opinions_select_'))
    def admin_opinions_select(call):
        uid = call.data.split('_')[2]
        data = bot.db.get(uid, {})
        opinions = data.get('opinions', [])
        text = f"Мнения о {data['full_name']} ({len(opinions)}):\n\n"
        for idx, op in enumerate(opinions):
            status = "✅" if op.get('approved') else "❌"
            text += f"{idx+1}. {op['text']} (@{op['author_username']}, {op['date']}) {status}\n\n"
        
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("➕ Добавить мнение вручную", callback_data=f"admin_add_opinion_{uid}"))
        kb.add(types.InlineKeyboardButton("❌ Удалить мнение", callback_data=f"admin_delete_opinion_{uid}"))

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

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
        if 'opinions' not in bot.db[uid]:
            bot.db[uid]['opinions'] = []
        bot.db[uid]['opinions'].append(opinion)
        bot.save_db(bot.db)
        bot.send_message(message.chat.id, "Мнение добавлено и одобрено!")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('admin_delete_opinion_'))
    def admin_delete_opinion_start(call):
        uid = call.data.split('_')[3]
        opinions = bot.db[uid].get('opinions', [])
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
        del bot.db[uid]['opinions'][idx]
        if not bot.db[uid]['opinions']:
            del bot.db[uid]['opinions']
        bot.save_db(bot.db)
        bot.edit_message_text("Мнение удалено.", call.message.chat.id, call.message.message_id)