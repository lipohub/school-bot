# utils.py
from telebot import types
import base64

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("Найти ученика", callback_data="search"))
    kb.add(types.InlineKeyboardButton("Дать наводку / добавить себя", callback_data="add_tip"))
    return kb

def get_students_kb(db, prefix: str = "", only_approved: bool = True):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for uid, data in sorted(db.items(), key=lambda x: x[1].get('full_name', '')):
        if only_approved and not data.get('approved', False):
            continue
        kb.add(types.InlineKeyboardButton(
            f"{data['full_name']} • {data['class']}",
            callback_data=f"{prefix}{uid}"
        ))
    return kb

def encode_query(q): 
    return base64.b64encode(q.encode()).decode()
def decode_query(q): 
    return base64.b64decode(q.encode()).decode()