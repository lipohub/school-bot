import telebot
from config import BOT_TOKEN
from database import load_db, save_db, generate_key
from handlers import register_all_handlers
from utils import main_menu, get_students_kb

bot = telebot.TeleBot(BOT_TOKEN)
bot.db = load_db()
bot.save_db = save_db
bot.generate_key = generate_key
bot.main_menu = main_menu
bot.get_students_kb = get_students_kb

# Регистрируем все обработчики
register_all_handlers(bot)

if __name__ == '__main__':
    print("Бот запущен! Структура — огонь!")
    bot.infinity_polling()