
import telebot
from config import BOT_TOKEN, ADMIN_IDS
from database import load_db, save_db, generate_key
from handlers import register_all_handlers

bot = telebot.TeleBot(BOT_TOKEN)

# Вешаем всё нужное прямо на объект бота
bot.db = load_db()
bot.save_db = save_db
bot.generate_key = generate_key
bot.config = type('Config', (), {'ADMIN_IDS': ADMIN_IDS})()

register_all_handlers(bot)

if __name__ == '__main__':
    print("Бот запущен! Структура — огонь!")
    try:
        bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
    except Exception as e:
        print("Ошибка polling:", e)