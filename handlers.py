# handlers.py — сюда кидаем ВСЁ, что было в старом bot.py кроме подключения к БД и токена
import telebot
from telebot import types
from datetime import datetime
import base64

from database import load_db, save_db, generate_key
from utils import main_menu, encode_query, decode_query
from config import ADMIN_IDS

# Глобальная переменная (будет обновляться)
db = load_db()

bot = telebot.TeleBot("DUMMY")  # токен возьмём из main.py потом