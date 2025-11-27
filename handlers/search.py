# handlers/search.py
from telebot import types
from utils import encode_query, decode_query

def register_handlers(bot):
    @bot.message_handler(commands=['search'])
    def search_command(message):
        msg = bot.send_message(message.chat.id, "Напиши фамилию или имя ученика:")
        bot.register_next_step_handler(msg, process_search)

    @bot.callback_query_handler(func=lambda c: c.data == 'search')
    def search_start(call):
        msg = bot.send_message(call.message.chat.id, "Напиши фамилию или имя ученика:")
        bot.register_next_step_handler(msg, process_search)

    def process_search(message):
        query = message.text.lower().strip() if message.text else ""
        if not query:
            bot.send_message(message.chat.id, "Запрос пустой", reply_markup=bot.utils.main_menu())
            return

        results = []
        for uid, data in bot.db.items():
            if not data.get('approved', False):
                continue
            fullname = data['full_name'].lower()
            cls = data.get('class', '').lower()
            if query in fullname or query in cls:
                results.append((uid, data))

        if not results:
            bot.send_message(message.chat.id, "Ничего не нашёл", reply_markup=bot.utils.main_menu())
            return

        results.sort(key=lambda x: x[1]['full_name'])
        show_page(message.chat.id, query, 1, results)

    def show_page(chat_id, query, page, results):
        per_page = 10
        total = (len(results) + per_page - 1) // per_page
        start = (page-1) * per_page
        chunk = results[start:start+per_page]

        kb = types.InlineKeyboardMarkup(row_width=1)
        for uid, data in chunk:
            kb.add(types.InlineKeyboardButton(f"{data['full_name']} • {data['class']}", callback_data=f"profile_{uid}"))

        nav = []
        enc = encode_query(query)
        if page > 1:
            nav.append(types.InlineKeyboardButton("◀️", callback_data=f"sp_{enc}_{page-1}"))
        if page < total:
            nav.append(types.InlineKeyboardButton("▶️", callback_data=f"sp_{enc}_{page+1}"))
        if nav: kb.row(*nav)

        text = f"Результаты по «{query}» ({page}/{total}):"
        bot.send_message(chat_id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('sp_'))
    def pagination(call):
        _, enc, page = call.data.split('_')
        query = decode_query(enc)
        page = int(page)

        results = []
        for uid, data in bot.db.items():
            if not data.get('approved', False): continue
            if query in data['full_name'].lower() or query in data.get('class', '').lower():
                results.append((uid, data))
        results.sort(key=lambda x: x[1]['full_name'])

        show_page(call.message.chat.id, query, page, results)
        bot.answer_callback_query(call.id)