from telebot import types
from datetime import datetime

def register_handlers(bot):
    @bot.message_handler(commands=['add_tip'])
    def add_tip(message):
        bot.send_message(message.chat.id, 
                        "Отправьте информацию об ученике одним сообщением в следующем формате:\n\n"
                        "Иванов Иван Иванович\n"
                        "10А\n"
                        "01.01.2005\n"
                        "8 999 123 45 67\n"
                        "@username\n"
                        "vk.com/username\n"
                        "Программирование, математика\n"
                        "Описание интересов и характеристик\n\n"
                        "Можно также прикрепить фотографию.")
        bot.register_next_step_handler(message, process_tip)

    def process_tip(message):
        text = message.text.strip() if message.text else ""
        photo_id = message.photo[-1].file_id if message.photo else None
        
        bot.send_message(message.chat.id, 
            "Спасибо! Я отправил твою наводку админам на проверку.", 
            reply_markup=bot.utils.main_menu())

        # Формируем сообщение админам с кнопками
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("Подтвердить наводку", callback_data=f"approve_tip_{message.message_id}"),
            types.InlineKeyboardButton("Отклонить", callback_data=f"reject_tip_{message.message_id}")
        )
        
        info = (f"Новая наводка от @{message.from_user.username} ({message.from_user.id})\n"
                f"Сообщение ID: {message.message_id}\n\n{text}")
        
        for admin in bot.config.ADMIN_IDS:
            if photo_id:
                bot.send_photo(admin, photo_id, caption=info, reply_markup=kb)
            else:
                bot.send_message(admin, info, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('approve_tip_') or c.data.startswith('reject_tip_'))
    def handle_tip_approval(call):
        if call.from_user.id not in bot.config.ADMIN_IDS:
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
            for uid, data in bot.db.items():
                if data.get('full_name', '').lower() == parsed_data['full_name'].lower() and data.get('class', '').lower() == parsed_data['class'].lower():
                    existing_uid = uid
                    break
            
            if existing_uid:
                # Обновляем существующий
                bot.db[existing_uid].update(parsed_data)
                uid = existing_uid
            else:
                # Создаем новый с генерированным ключом
                uid = bot.generate_key(parsed_data['full_name'], parsed_data['class'])
                bot.db[uid] = parsed_data
            
            bot.db[uid]['approved'] = True
            if photo_id:
                bot.db[uid]['photo_id'] = photo_id
            if 'opinions' not in bot.db[uid]:
                bot.db[uid]['opinions'] = []
            bot.save_db(bot.db)
            
            bot.edit_message_text(f"Наводка {action} админом @{call.from_user.username}. Профиль {'обновлен' if existing_uid else 'добавлен'}.", 
                                call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(f"Наводка {action} админом @{call.from_user.username}", 
                                call.message.chat.id, call.message.message_id)