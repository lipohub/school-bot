# main.py
import telebot
from config import BOT_TOKEN
from database import load_db, save_db
from handlers import register_all_handlers

bot = telebot.TeleBot(BOT_TOKEN)
db = load_db()

# Регистрируем ВСЕ хендлеры одним вызовом
register_all_handlers(bot)

if __name__ == '__main__':
    print("Бот запущен! Структура — огонь!")
    bot.infinity_polling()