from telebot import types
from database import generate_key
import re

def parse_tip(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if len(lines) < 2:
        return None
    
    parsed = {
        'full_name': lines[0],
        'class': lines[1],
        'birthday': lines[2] if len(lines) > 2 else '',
        'phone': lines[3] if len(lines) > 3 else '',
        'tg': lines[4] if len(lines) > 4 else '',
        'vk': lines[5] if len(lines) > 5 else '',
        'interests': lines[6] if len(lines) > 6 else '',
        'description': '\n'.join(lines[7:]) if len(lines) > 7 else ''
    }
    return parsed

def register_handlers(bot):
    @bot.message_handler(commands=['add_tip'])
    def add_tip(message):
        bot.send_message(message.chat.id, 
                        "Отправьте информацию об ученике одним сообщением в следующем формате:\n\n"
                        "Иванов Иван Иванович\n"
                        "10А\n"
                        "01.01.2005\n"
                        "8 999 123 45 67\n"
                        "@username\n"
                        "vk.com/username\n"
                        "Программирование, математика\n"
                        "Описание интересов и характеристик")
        bot.register_next_step_handler(message, process_tip)

    def process_tip(message):
        if not message.text:
            bot.send_message(message.chat.id, "Сообщение не может быть пустым. Попробуйте снова.")
            bot.register_next_step_handler(message, process_tip)
            return

        parsed_data = parse_tip(message.text)
        if not parsed_data:
            bot.send_message(message.chat.id, 
                           "Ошибка в формате сообщения. Убедитесь, что вы отправили информацию в правильном формате.")
            bot.register_next_step_handler(message, process_tip)
            return

        uid = generate_key(parsed_data['full_name'], parsed_data['class'])
        
        # Создаем запись с данными
        bot.db[uid] = parsed_data
        bot.db[uid]['approved'] = False  # Новые записи требуют одобрения
        
        # Сохраняем в базу данных
        save_db(bot.db)
        
        bot.send_message(message.chat.id, 
                        f"Информация о {parsed_data['full_name']} добавлена и отправлена на проверку администратору.")