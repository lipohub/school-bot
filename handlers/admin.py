# handlers/admin.py
from telebot import types

def register_handlers(bot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id not in bot.config.ADMIN_IDS:
            bot.reply_to(message, "Доступ запрещён")
            return
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("Добавить", callback_data="admin_add"),
            types.InlineKeyboardButton("Список", callback_data="admin_list")
        )
        kb.add(types.InlineKeyboardButton("Экспорт", callback_data="admin_export"))
        bot.send_message(message.chat.id, "Админ-панель", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == 'admin_export')
    def export(call):
        if call.from_user.id not in bot.config.ADMIN_IDS: return
        import json, os
        with open('export.json', 'w', encoding='utf-8') as f:
            json.dump(bot.db, f, ensure_ascii=False, indent=2)
        with open('export.json', 'rb') as f:
            bot.send_document(call.message.chat.id, f)
        os.remove('export.json')