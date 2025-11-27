# handlers/__init__.py
# Этот файл должен быть пустым или содержать только это:

from .start import register_handlers as reg_start
from .search import register_handlers as reg_search
from .profile import register_handlers as reg_profile
from .tip import register_handlers as reg_tip
from .opinion import register_handlers as reg_opinion
from .admin import register_handlers as reg_admin

def register_all_handlers(bot):
    reg_start(bot)
    reg_search(bot)
    reg_profile(bot)
    reg_tip(bot)
    reg_opinion(bot)
    reg_admin(bot)
