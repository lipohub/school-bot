# handlers/opinion.py
from telebot import types
from datetime import datetime

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda c: c.data.startswith('add_opinion_'))
    def add_opinion(call):
        uid = call.data.split('_')[2]
        msg = bot.send_message(call.message.chat.id, "Напиши мнение (до 200 символов):")
        bot.register_next_step_handler(msg, save_opinion, uid)

    def save_opinion(message, uid):
        text = message.text.strip()
        if len(text) > 200:
            bot.send_message(message.chat.id, "Слишком длинно!")
            return
        if 'opinions'] = bot.db.setdefault(uid, {}).setdefault('opinions', [])
        bot.db[uid]['opinions'].append({
            'text': text,
            'author_id': str(message.from_user.id),
            'author_username': message.from_user.username or "аноним",
            'date': datetime.now().strftime("%d.%m.%Y"),
            'approved': False
        })
        bot.save_db(bot.db)
        bot.send_message(message.chat.id, "Мнение отправлено на модерацию!")