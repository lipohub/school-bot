import telebot
from config import BOT_TOKEN, ADMIN_IDS
from database import load_db, save_db, generate_key
from handlers import register_all_handlers

bot = telebot.TeleBot(BOT_TOKEN)

# Прикрепляем всё к боту
bot.db = load_db()
bot.save_db = save_db
bot.generate_key = generate_key
bot.config = type('Config', (), {'ADMIN_IDS': ADMIN_IDS})()  # удобный доступ

# Регистрация всех обработчиков
register_all_handlers(bot)

if __name__ == '__main__':
    print("Бот запущен! Структура — огонь!")
    # Эти параметры решают проблему 409 Conflict навсегда
    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30,
        allowed_updates=[]  # ускоряет polling
    )