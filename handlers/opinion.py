
# handlers/opinion.py
from telebot import types
from datetime import datetime

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda c: c.data.startswith('add_opinion_'))
    def add_opinion(call):
        uid = call.data.split('_')[2]
        msg = bot.send_message(call.message.chat.id, "Напиши мнение (до 200 символов):")
        bot.register_next_step_handler(msg, save_opinion, uid, call.message.chat.id)

    def save_opinion(message, uid, chat_id):
        text = message.text.strip()
        if len(text) > 200:
            bot.send_message(message.chat.id, "Слишком длинно! Мнение не может превышать 200 символов.")
            return
        
        # Исправлена синтаксическая ошибка
        if uid not in bot.db:
            bot.db[uid] = {}
        if 'opinions' not in bot.db[uid]:
            bot.db[uid]['opinions'] = []
        
        bot.db[uid]['opinions'].append({
            'text': text,
            'author_id': str(message.from_user.id),
            'author_username': message.from_user.username or "аноним",
            'date': datetime.now().strftime("%d.%m.%Y"),
            'approved': False
        })
        
        save_db(bot.db)  # Используем функцию из database
        bot.send_message(chat_id, "Мнение отправлено на модерацию!")