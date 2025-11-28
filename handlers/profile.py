# handlers/profile.py
from telebot import types

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda c: c.data.startswith('profile_'))
    def show_profile(call):
        uid = call.data.split('_')[1]
        bot.refresh_db()  # Обновляем данные из базы
        data = bot.db.get(uid)

        if not data or not data.get('approved', False):
            bot.answer_callback_query(call.id, "Профиль не подтверждён")
            return

        text = f"*{data['full_name']}*\nКласс: {data['class']}\n"
        if data.get('birthday'): text += f"ДР: {data['birthday']}\n"
        if data.get('phone'): text += f"Телефон: {data['phone']}\n"
        if data.get('tg'): text += f"ТГ: {data['tg']}\n"
        if data.get('vk'): text += f"ВК: {data['vk']}\n"
        if data.get('interests'): text += f"Интересы: {data['interests']}\n"
        if data.get('description'): text += f"\n{data['description']}"

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("Назад", callback_data="search"))
        kb.add(types.InlineKeyboardButton("Добавить мнение", callback_data=f"add_opinion_{uid}"))

        opinions = [op for op in data.get('opinions', []) if op.get('approved')]
        if opinions:
            kb.add(types.InlineKeyboardButton(f"Мнения ({len(opinions)})", callback_data=f"opinions_{uid}_1"))

        if data.get('photo_id'):
            bot.send_photo(call.message.chat.id, data['photo_id'], caption=text, parse_mode='Markdown', reply_markup=kb)
        else:
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=kb)