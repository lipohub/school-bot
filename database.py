# database.py
import pymongo
import hashlib
from config import MONGO_URI

client = pymongo.MongoClient(MONGO_URI)
db = client['telegram_bot_db']
collection = db['students']

def load_db():
    doc = collection.find_one({'_id': 'students'})
    return doc['data'] if doc else {}

def save_db(data):
    collection.update_one(
        {'_id': 'students'},
        {'$set': {'data': data}},
        upsert=True
    )

def generate_key(name, class_name):
    return hashlib.md5(f"{name.lower()}_{class_name.lower()}".encode()).hexdigest()