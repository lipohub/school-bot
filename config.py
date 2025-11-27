# config.py
import os

BOT_TOKEN = "8483130885:AAEBgryQXbUnNUuS22ZJeUdQVOo4Jua6Vx0"
ADMIN_IDS = [1967855685]  # ← сюда можно добавить ещё админов через запятую

MONGO_URI = os.getenv("MONGO_URI')
if not MONGO_URI:
    raise ValueError("Ошибка: MONGO_URI не найден! Зайди в Render → Environment → добавь переменную MONGO_URI")