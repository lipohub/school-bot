from telebot import types
from utils import main_menu

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(message.chat.id,
            "Привет! Это поисковик учеников нашей школы\n\n"
            "Тут можно найти инфу о человеке или оставить заявку на добавление/исправление данных.\n\n"
            "Доступные команды:\n/start • /search • /add_tip • /admin • /help",
            reply_markup=main_menu())

    @bot.message_handler(commands=['help'])
    def help_command(message):
        bot.send_message(message.chat.id, "Доступные команды:\n/start — главное меню\n/search — поиск\n/add_tip — дать наводку\n/admin — админка")