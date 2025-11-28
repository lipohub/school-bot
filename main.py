# main.py
import telebot
from config import BOT_TOKEN, ADMIN_IDS
from database import load_db, save_db
from handlers import register_all_handlers

# Создаем экземпляр бота
bot = telebot.TeleBot(BOT_TOKEN)

# Загружаем данные из MongoDB при запуске
bot.db = load_db()

# Добавляем необходимые атрибуты к объекту бота
bot.config = type('Config', (), {'ADMIN_IDS': ADMIN_IDS})()
bot.save_db = save_db  # Функция для сохранения данных в базу

# Регистрируем все обработчики
register_all_handlers(bot)

if __name__ == '__main__':
    print("Бот запущен!")
    print(f"Загружено записей из базы данных: {len(bot.db)}")
    bot.infinity_polling()