# config.py
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [1967855685]  # Список ID администраторов

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("Ошибка: переменная MONGO_URI не установлена")