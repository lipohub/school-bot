# handlers/tip.py
from telebot import types
from database import generate_key
from utils import main_menu

def parse_tip(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) < 2: return None
    return {
        'full_name': lines[0],
        'class': lines[1],
        'birthday': lines[2] if len(lines)>2 else '',
        'phone': lines[3] if len(lines)>3 else '',
        'tg': lines[4] if len(lines)>4 else '',
        'vk': lines[5] if len(lines)>5 else '',
        'interests': lines[6] if len(lines)>6 else '',
        'description': '\n'.join(lines[7:]) if len(lines)>7 else ''
    }

def register_handlers(bot):
    @bot.message_handler(commands=['add_tip'])
    @bot.callback_query_handler(func=lambda c: c.data == 'add_tip')
    def add_tip_entry(point):
        if hasattr(point, 'message'):
            chat_id = point.message.chat.id
        else:
            chat_id = point.message.chat.id
        msg = bot.send_message(chat_id, "Пришли данные одним сообщением (пример в /start)\nМожно с фото")
        bot.register_next_step_handler(msg, process_tip)

    def process_tip(message):
        text = message.text or ""
        photo = message.photo[-1].file_id if message.photo else None

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Подтвердить", callback_data=f"apptip_{message.message_id}"))
        kb.add(types.InlineKeyboardButton("Отклонить", callback_data=f"rejt_ip_{message.message_id}"))

        for admin_id in bot.config.ADMIN_IDS:
            if photo:
                bot.send_photo(admin_id, photo, caption=f"Наводка от {message.from_user.id}\n\n{text}", reply_markup=kb)
            else:
                bot.send_message(admin_id, f"Наводка от {message.from_user.id}\n\n{text}", reply_markup=kb)

        bot.send_message(message.chat.id, "Спасибо! Наводка у админов на проверке", reply_markup=main_menu())

    @bot.callback_query_handler(func=lambda c: c.data.startswith(('apptip_', 'rejt_ip_')))
    def tip_moderation(call):
        if call.from_user.id not in bot.config.ADMIN_IDS:
            return
        approve = call.data.startswith('apptip_')
        msg_id = call.data.split('_')[1]
        # Здесь упрощённая версия — в реальном коде надо хранить сообщение и парсить
        bot.edit_message_text("Обработка наводки — пока заглушка", call.message.chat.id, call.message.message_id)