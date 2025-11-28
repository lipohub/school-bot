# handlers/opinion.py
from telebot import types
from datetime import datetime

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda c: c.data.startswith('add_opinion_'))
    def add_opinion_start(call):
        uid = call.data.split('_')[2]
        if uid not in bot.db:
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
        if "opinions" not in bot.db[uid]:
            bot.db[uid]["opinions"] = []

        opinion = {
            "text": text,
            "author_id": str(message.from_user.id),
            "author_username": message.from_user.username or 'без_юзернейма',
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "approved": False
        }
        bot.db[uid]["opinions"].append(opinion)
        bot.save_db(bot.db)
        idx = len(bot.db[uid]["opinions"]) - 1

        # Сообщение админам с кнопками
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("Подтвердить", callback_data=f"approve_op_{uid}_{idx}"),
            types.InlineKeyboardButton("Отклонить", callback_data=f"reject_op_{uid}_{idx}")
        )
        
        info = (f"Новое мнение о {bot.db[uid].get('full_name', 'ID '+uid)}\n"
                f"От: @{message.from_user.username} ({message.from_user.id})\n\n{text}")
        
        for admin in bot.config.ADMIN_IDS:
            bot.send_message(admin, info, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('approve_op_') or c.data.startswith('reject_op_'))
    def handle_opinion_approval(call):
        if call.from_user.id not in bot.config.ADMIN_IDS:
            bot.answer_callback_query(call.id, "Ты не админ")
            return

        parts = call.data.split('_')
        action = parts[0]
        uid = parts[2]
        index = int(parts[3])

        if uid not in bot.db or index >= len(bot.db[uid].get("opinions", [])):
            bot.answer_callback_query(call.id, "Мнение не найдено")
            return

        if action == 'approve':
            bot.db[uid]["opinions"][index]["approved"] = True
            bot.save_db(bot.db)
            bot.edit_message_text(f"Мнение подтверждено админом @{call.from_user.username}\nТеперь видно всем!", 
                                  call.message.chat.id, call.message.message_id)
        else:
            del bot.db[uid]["opinions"][index]
            if not bot.db[uid]["opinions"]:
                del bot.db[uid]["opinions"]
            bot.save_db(bot.db)
            bot.edit_message_text(f"Мнение отклонено админом @{call.from_user.username}", 
                                  call.message.chat.id, call.message.message_id)