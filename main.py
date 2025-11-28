# main.py
import telebot
from config import BOT_TOKEN
from database import load_db, save_db, generate_key, db

bot = telebot.TeleBot(BOT_TOKEN)
bot.db = db

# Регистрируем все обработчики
from handlers import register_all_handlers
register_all_handlers(bot)

if __name__ == '__main__':
    print("Бот запущен! Структура — огонь!")
    bot.infinity_polling()