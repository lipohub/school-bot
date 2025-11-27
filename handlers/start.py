# handlers/start.py
def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(message.chat.id,
            "Привет! Это поисковик учеников нашей школы\n\n"
            "Тут можно найти инфу о человеке или оставить заявку на добавление/исправление данных.\n\n"
            "Доступные команды:\n"
            "/start - Главное меню\n"
            "/search - Поиск ученика\n"
            "/add_tip - Дать наводку\n"
            "/admin - Админ-панель (только для админов)\n"
            "/help - Список команд",
            reply_markup=main_menu())

    @bot.message_handler(commands=['help'])
    def help_command(message):
        bot.send_message(message.chat.id,
            "Доступные команды:\n"
            "/start - Главное меню\n"
            "/search - Поиск ученика\n"
            "/add_tip - Дать наводку\n"
            "/admin - Админ-панель (только для админов)\n"
            "/help - Этот список")