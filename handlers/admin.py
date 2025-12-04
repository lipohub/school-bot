# handlers/admin.py
import json
from telebot import types
from database import load_db, save_db

# Состояния для импорта (чтобы бот знал, от кого ждёт файл)
import_states = {}  # {user_id: True}

def register_handlers(bot):

    # ===================== АДМИН-ПАНЕЛЬ =====================
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id not in bot.config.ADMIN_IDS:
            return bot.reply_to(message, "Доступ запрещён")

        total = len(bot.db)
        approved = sum(1 for v in bot.db.values() if v.get('approved'))

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("Статистика", callback_data="adm_stats"),
            types.InlineKeyboardButton("Все записи", callback_data="adm_list_1")
        )
        kb.add(
            types.InlineKeyboardButton("Рассылка", callback_data="adm_broadcast"),
            types.InlineKeyboardButton("Перезагрузить БД", callback_data="adm_reload")
        )
        kb.add(
            types.InlineKeyboardButton("Импорт старой базы", callback_data="adm_import_start")
        )

        bot.send_message(message.chat.id,
            f"<b>Админ-панель</b>\n\n"
            f"Всего записей: {total}\n"
            f"Одобрено: {approved}\n"
            f"На модерации: {total - approved}",
            parse_mode='HTML', reply_markup=kb)

    # ===================== СТАТИСТИКА =====================
    @bot.callback_query_handler(func=lambda c: c.data == 'adm_stats')
    def stats(call):
        if call.from_user.id not in bot.config.ADMIN_IDS: return
        total = len(bot.db)
        approved = sum(1 for v in bot.db.values() if v.get('approved'))
        bot.answer_callback_query(call.id, f"Всего: {total} | Одобрено: {approved}", show_alert=True)

    # ===================== ПЕРЕЗАГРУЗКА БД =====================
    @bot.callback_query_handler(func=lambda c: c.data == 'adm_reload')
    def reload_db(call):
        if call.from_user.id not in bot.config.ADMIN_IDS: return
        bot.db = load_db()
        bot.answer_callback_query(call.id, "База перезагружена из MongoDB")
        admin_panel(call.message)

    # ===================== ИМПОРТ СТАРОЙ БАЗЫ =====================
    @bot.callback_query_handler(func=lambda c: c.data == 'adm_import_start')
    def import_start(call):
        if call.from_user.id not in bot.config.ADMIN_IDS: return
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, 
            "Пришли мне JSON-файл со старой базой (одним сообщением).\n"
            "Формат: как ты раньше сохранял — {uid: {данные}}")
        import_states[call.from_user.id] = True
        bot.register_next_step_handler(msg, process_import)

    def process_import(message):
        user_id = message.from_user.id
        if user_id not in import_states:
            return
        import_states.pop(user_id, None)

        if not message.document:
            bot.reply_to(message, "Пришли именно файл .json")
            return

        if not message.document.file_name.lower().endswith('.json'):
            bot.reply_to(message, "Нужен именно .json файл")
            return

        try:
            file_info = bot.get_file(message.document.file_id)
            file_content = bot.download_file(file_info.file_path)
            data = json.loads(file_content.decode('utf-8'))

            if not isinstance(data, dict):
                bot.reply_to(message, "Ошибка: в файле должен быть объект {}")
                return

            added = 0
            updated = 0
            for uid, record in data.items():
                if not isinstance(record, dict):
                    continue
                # Автоматически одобряем при импорте
                record['approved'] = True
                if uid not in bot.db:
                    added += 1
                else:
                    updated += 1
                bot.db[uid] = record

            bot.save_db(bot.db)
            bot.db = load_db()  # перезагружаем, чтобы всё точно было свежим

            bot.reply_to(message,
                f"Импорт завершён!\n"
                f"Добавлено: {added}\n"
                f"Обновлено: {updated}\n"
                f"Всего в базе: {len(bot.db)}")
            
            admin_panel(message)

        except Exception as e:
            bot.reply_to(message, f"Ошибка при импорте: {e}")

    # ===================== СПИСОК ЗАПИСЕЙ =====================
    @bot.callback_query_handler(func=lambda c: c.data.startswith('adm_list_'))
    def list_all(call):
        if call.from_user.id not in bot.config.ADMIN_IDS: return
        page = int(call.data.split('_')[-1])
        items = sorted(bot.db.items(), key=lambda x: x[1].get('full_name', ''))
        per_page = 10
        start = (page-1)*per_page
        end = start + per_page
        chunk = items[start:end]

        kb = types.InlineKeyboardMarkup(row_width=1)
        for uid, data in chunk:
            status = "Одобрено" if data.get('approved') else "На модерации"
            kb.add(types.InlineKeyboardButton(
                f"{status} {data.get('full_name', uid)} • {data.get('class', '?')}",
                callback_data=f"adm_prof_{uid}"
            ))
        nav = []
        if page > 1: nav.append(types.InlineKeyboardButton("Назад", callback_data=f"adm_list_{page-1}"))
        if end < len(items): nav.append(types.InlineKeyboardButton("Вперёд", callback_data=f"adm_list_{page+1}"))
        if nav: kb.row(*nav)
        kb.add(types.InlineKeyboardButton("Назад в админку", callback_data="adm_back"))

        bot.edit_message_text(f"Все записи (стр. {page})", call.message.chat.id,
                              call.message.message_id, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == 'adm_back')
    def back_to_admin(call):
        if call.from_user.id not in bot.config.ADMIN_IDS: return
        admin_panel(call.message)

    # Удаление профиля и другие функции (как было раньше) — можно оставить или добавить по желанию