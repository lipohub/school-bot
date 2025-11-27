# utils.py
from telebot import types
import base64

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Найти ученика", callback_data="search"))
    kb.add(types.InlineKeyboardButton("Дать наводку", callback_data="add_tip"))
    return kb

def encode_query(q): return base64.b64encode(q.encode()).decode()
def decode_query(q): return base64.b64decode(q.encode()).decode()