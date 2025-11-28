
# main.py
import telebot
from config import BOT_TOKEN, ADMIN_IDS
from database import load_db, save_db
from handlers import register_all_handlers

bot = telebot.TeleBot(BOT_TOKEN)
bot.db = load_db()  # Сохраняем базу данных как атрибут бота
bot.config = type('Config', (), {'ADMIN_IDS': ADMIN_IDS})()  # Создаем объект конфигурации

def refresh_db():
    """Обновляет данные в bot.db"""
    bot.db = load_db()

# Добавляем функцию сохранения как атрибут бота
def save_bot_db(data):
    save_db(data)
    bot.db = data  # Обновляем локальную копию

bot.save_db = save_bot_db  # Присваиваем функцию боту
bot.refresh_db = refresh_db  # Присваиваем функцию обновления

# Регистрируем все хендлеры
register_all_handlers(bot)

if __name__ == '__main__':
    print("Бот запущен!")
    bot.infinity_polling()