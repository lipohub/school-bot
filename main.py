# main.py — ЭТО ТЕПЕРЬ ГЛАВНЫЙ ФАЙЛ ДЛЯ ЗАПУСКА
import telebot
from config import BOT_TOKEN, ADMIN_IDS
from database import load_db, save_db
import handlers

# Подменяем токен и базу в handlers
handlers.bot = telebot.TeleBot(BOT_TOKEN)
handlers.db = load_db()

# Чтобы база всегда была свежая при изменениях
def refresh_db():
    handlers.db = load_db()

handlers.refresh_db = refresh_db
handlers.save_db = save_db
handlers.ADMIN_IDS = ADMIN_IDS

if __name__ == '__main__':
    print("Бот запущен и готов к работе!")
    handlers.bot.infinity_polling()