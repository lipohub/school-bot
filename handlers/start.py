from telebot import types
from utils import main_menu

def register_handlers(bot):
    @bot.message_handler(commands=['start', 'help'])
    def start(message):
        bot.send_message(message.chat.id, "Добро пожаловать! Выбери действие:", reply_markup=main_menu())