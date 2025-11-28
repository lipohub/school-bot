# handlers/tip.py
from telebot import types

def register_handlers(bot):
    @bot.message_handler(commands=['add_tip'])
    def add_tip_command(message):
        msg = bot.send_message(message.chat.id,
            "Напиши одним сообщением всё, что знаешь или хочешь исправить.\n"
            "Формат (пример):\n\n"
            "Иванов Иван\n10А\n15.03.2008\n+79991234567\n@ivanov_tg\nvk.com/ivanov2008\nфутбол, программирование\nОписание: Крутой парень, любит кодинг.\n\n"
            "Можешь прикрепить фото.")
        
        bot.register_next_step_handler(msg, process_tip, message.from_user.id)

    def process_tip(message, user_id):
        tip_text = message.text.strip() if message.text else ""
        photo_id = message.photo[-1].file_id if message.photo else None
        
        bot.send_message(message.chat.id, 
            "Спасибо! Я отправил твою наводку админам на проверку.\n"
            "Как только проверят — информация появится в поиске.", 
            reply_markup=bot.utils.main_menu())

        # Формируем сообщение админам с кнопками
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("Подтвердить наводку", callback_data=f"approve_tip_{message.message_id}"),
            types.InlineKeyboardButton("Отклонить", callback_data=f"reject_tip_{message.message_id}"))
        
        info = (f"Новая наводка от @{message.from_user.username} ({message.from_user.id})\n"
                f"Сообщение ID: {message.message_id}\n\n{tip_text}")
        
        for admin in bot.config.ADMIN_IDS:
            if photo_id:
                bot.send_photo(admin, photo_id, caption=info, reply_markup=kb)
            else:
                bot.send_message(admin, info, reply_markup=kb)