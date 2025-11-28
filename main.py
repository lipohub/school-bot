import telebot
from config import BOT_TOKEN, ADMIN_IDS
from database import load_db, save_db
from handlers import register_all_handlers

bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация необходимых атрибутов
bot.db = load_db()
bot.config = type('Config', (), {'ADMIN_IDS': ADMIN_IDS})()
bot.save_db = save_db

# Регистрируем все обработчики
register_all_handlers(bot)

if __name__ == '__main__':
    print("Бот запущен!")
    bot.infinity_polling()