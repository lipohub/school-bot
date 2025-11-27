# main.py
import telebot
from config import BOT_TOKEN
import handlers

# Подключаем реальный бот и базу
handlers.bot = telebot.TeleBot(BOT_TOKEN)
handlers.db = handlers.load_db()  # загрузили базу

# Функция для обновления базы при изменениях
def refresh_db():
    handlers.db = handlers.load_db()

handlers.refresh_db = refresh_db
handlers.save_db = handlers.save_db

if __name__ == '__main__':
    print("Бот запущен!")
    handlers.bot.infinity_polling()