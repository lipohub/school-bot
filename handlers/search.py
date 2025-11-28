# handlers/search.py
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
        query = message.text.lower().strip()
        if not query:
            bot.send_message(message.chat.id, "Запрос пустой 😔", reply_markup=bot.utils.main_menu())
            return

        results = []
        for uid, data in bot.db.items():
            if not data.get('approved', False):
                continue
            if query in data['full_name'].lower() or query in data.get('class', '').lower():
                results.append((uid, data))

        if not results:
            bot.send_message(message.chat.id, "Ничего не нашёл 😔", reply_markup=bot.utils.main_menu())
            return

        results = sorted(results, key=lambda x: x[1]['full_name'])

        per_page = 10
        total_pages = (len(results) + per_page - 1) // per_page

        show_search_page(message.chat.id, query, 1, results, total_pages, message_id=None)

    def show_search_page(chat_id, query, page, results, total_pages, message_id=None):
        per_page = 10
        start = (page - 1) * per_page
        end = start + per_page
        current_results = results[start:end]

        kb = types.InlineKeyboardMarkup(row_width=1)
        for uid, data in current_results:
            kb.add(types.InlineKeyboardButton(
                f"{data['full_name']} • {data['class']}",
                callback_data=f"profile_{uid}"
            ))

        row = []
        encoded_query = base64.b64encode(query.encode()).decode('utf-8')
        if page > 1:
            row.append(types.InlineKeyboardButton("◀️ Prev", callback_data=f"search_page_{encoded_query}_{page-1}"))
        if page < total_pages:
            row.append(types.InlineKeyboardButton("Next ▶️", callback_data=f"search_page_{encoded_query}_{page+1}"))
        if row:
            kb.row(*row)

        text = f"Выбери человека для '{query}' (страница {page}/{total_pages}):"

        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
        else:
            bot.send_message(chat_id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('search_page_'))
    def handle_search_page(call):
        parts = call.data.split('_')
        encoded_query = parts[2]
        page = int(parts[3])
        query = base64.b64decode(encoded_query).decode('utf-8')

        results = []
        for uid, data in bot.db.items():
            if not data.get('approved', False):
                continue
            if query in data['full_name'].lower() or query in data.get('class', '').lower():
                results.append((uid, data))

        results = sorted(results, key=lambda x: x[1]['full_name'])

        total_pages = (len(results) + 10 - 1) // 10

        if page < 1 or page > total_pages:
            bot.answer_callback_query(call.id, "Неверная страница")
            return

        show_search_page(call.message.chat.id, query, page, results, total_pages, call.message.message_id)