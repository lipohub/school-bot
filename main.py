# main.py
import telebot
from config import BOT_TOKEN
from database import load_db, save_db, generate_key
from handlers import register_all_handlers

bot = telebot.TeleBot(BOT_TOKEN)
bot.db = load_db()
bot.save_db = save_db
bot.generate_key = generate_key

# Регистрируем все обработчики
register_all_handlers(bot)

if __name__ == '__main__':
    print("Бот запущен!")
    bot.infinity_polling()