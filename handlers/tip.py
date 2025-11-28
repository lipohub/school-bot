from telebot import types
from datetime import datetime
from database import generate_key

def register_handlers(bot):
    @bot.message_handler(commands=['add_tip'])
    def add_tip(message):
        bot.send_message(message.chat.id, "Отправь наводку:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_tip)

    def process_tip(message):
        parsed = parse_tip(message.text)
        if parsed:
            uid = generate_key(parsed['full_name'], parsed['class'])
            bot.db[uid] = parsed
            bot.db[uid]['approved'] = False
            bot.database.save_db(bot.db)
            bot.send_message(message.chat.id, "Наводка сохранена и ожидает одобрения!")
        else:
            bot.send_message(message.chat.id, "Ошибка парсинга. Попробуй заново.")

#grok:render type="render_inline_citation"
<argument name="citation_id">1</argument>
</grok:render> 

### handlers/search.py
```python
from telebot import types
from utils import encode_query, decode_query

def register_handlers(bot):
    @bot.message_handler(commands=['search'])
    def search(message):
        bot.send_message(message.chat.id, "Введи запрос для поиска:")
        bot.register_next_step_handler(message, process_search)

    def process_search(message):
        query = message.text.strip().lower()
        if not query:
            bot.send_message(message.chat.id, "Запрос пустой.")
            return
        results = [ (uid, data) for uid, data in bot.db.items() if data.get('approved') and (query in data['full_name'].lower() or query in data['class'].lower()) ]
        if not results:
            bot.send_message(message.chat.id, "Ничего не найдено.")
            return
        show_search_page(message.chat.id, query, 1, results)