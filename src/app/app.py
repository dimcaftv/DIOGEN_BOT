from telebot import TeleBot

import messages.messages
import settings
from app.app_manager import AppManager
from database import database
from handlers import callback_handlers, message_handlers
from menu import menu
from utils import commands, filters


class App:
    def __init__(self):
        self.bot = TeleBot(settings.BOT_TOKEN)
        self.menu = menu.Menu(settings.pages_list, settings.actions_list)
        self.db = database.DatabaseInterface(settings.TMP_USER_DATA_PATH)
        self.app_manager = AppManager(self)

    def start(self):
        self.init_bot()
        self.startup_actions()
        self.bot.infinity_polling(skip_pending=True)
        self.stop_actions()

    def init_bot(self):
        self.register_bot_handlers()
        self.bot.current_states = self.db.dynamic_user_data.storage.storage

    def register_bot_handlers(self):
        message_handlers.register_handlers(self.bot, settings.cmd_handlers, settings.kwargs_handlers)
        callback_handlers.register_handlers(self.bot, settings.callbacks_handlers)
        filters.register_filters(self.bot, settings.bot_filters)
        commands.register_commands(self.bot, settings.commands_list)

    def set_bot_status(self, status: bool):
        self.bot.set_my_short_description(messages.messages.get_status_text(status))

    def startup_actions(self):
        self.set_bot_status(True)

    def stop_actions(self):
        self.set_bot_status(False)
        self.db.commit()
