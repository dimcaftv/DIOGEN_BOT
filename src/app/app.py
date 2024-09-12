import threading

from telebot import TeleBot

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
        self.db = database.DatabaseInterface()
        self.app_manager = AppManager(self)

    def start(self):
        self.init_bot()
        self.startup_actions()
        self.start_comands_waiting()
        self.bot.infinity_polling(skip_pending=True)
        self.stop_actions()

    def init_bot(self):
        self.register_bot_handlers()
        self.bot.enable_saving_states('../.state-save/states.pkl')

    def register_bot_handlers(self):
        message_handlers.register_handlers(self.bot, settings.cmd_handlers, settings.kwargs_handlers)
        callback_handlers.register_handlers(self.bot, settings.callbacks_handlers)
        filters.register_filters(self.bot, settings.bot_filters)
        commands.register_commands(self.bot, settings.commands_list)

    def command_handler(self):
        while True:
            cmd = input('>>> ')
            if cmd == 'stop':
                self.bot.stop_bot()
                break

    def start_comands_waiting(self):
        threading.Thread(target=self.command_handler).start()

    def set_bot_status(self, status: bool):
        opts = ['🔴', '🟢']
        d = f"Статус: {opts[status]}\n\nНовости: @diogen_bot_news\nКод: https://github.com/dimcaftv/DIOGEN_BOT"
        self.bot.set_my_short_description(d)

    def startup_actions(self):
        self.set_bot_status(True)

    def stop_actions(self):
        self.set_bot_status(False)
        self.db.commit()
