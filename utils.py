# utils.py
from telebot import types
import base64

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🔍 Найти ученика", callback_data="search"))
    kb.add(types.InlineKeyboardButton("➕ Дать наводку / добавить себя", callback_data="add_tip"))
    return kb

def get_students_kb(prefix):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for uid, data in sorted(bot.db.items(), key=lambda x: x[1]['full_name']):
        if data.get('approved', False):
            kb.add(types.InlineKeyboardButton(
                f"{data['full_name']} • {data['class']}",
                callback_data=f"{prefix}{uid}"
            ))
    return kb