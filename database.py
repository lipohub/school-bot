# database.py
import pymongo
import hashlib
from config import MONGO_URI

# Подключение к MongoDB
client = pymongo.MongoClient(MONGO_URI)
mongo_db = client['telegram_bot_db']
collection = mongo_db['students']

def load_db():
    """Загружает данные из MongoDB. Если данных нет, возвращает пустой словарь."""
    doc = collection.find_one({'_id': 'students'})
    if doc and 'data' in doc:
        return doc['data']
    else:
        # Если документа нет или в нем нет поля data, возвращаем пустой словарь
        return {}

def save_db(data):
    """Сохраняет данные в MongoDB."""
    collection.update_one(
        {'_id': 'students'},
        {'$set': {'data': data}},
        upsert=True  # Создает документ, если его нет
    )

def generate_key(full_name: str, class_name: str) -> str:
    """Генерирует уникальный ключ для студента на основе ФИО и класса."""
    key = f"{full_name.lower()}_{class_name.lower()}"
    return hashlib.md5(key.encode()).hexdigest()

def refresh_db():
    """Перезагружает данные из MongoDB."""
    return load_db()