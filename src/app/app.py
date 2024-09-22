from telebot.async_telebot import AsyncTeleBot

import messages.messages
import settings
from app.app_manager import AppManager
from database import database
from handlers import callback_handlers, message_handlers
from menu import menu
from utils import commands, filters


class App:
    def __init__(self):
        self.bot = AsyncTeleBot(settings.BOT_TOKEN)
        self.menu = menu.Menu(settings.pages_list, settings.actions_list)
        self.db = database.DatabaseInterface(settings.TMP_USER_DATA_PATH)
        self.app_manager = AppManager(self)

    async def start(self):
        await self.db.db.create_all_tables()
        await self.init_bot()
        await self.startup_actions()
        await self.bot.polling(non_stop=True, skip_pending=True)
        await self.stop_actions()

    async def init_bot(self):
        await self.register_bot_handlers()
        self.bot.current_states = self.db.dynamic_user_data.storage.storage

    async def register_bot_handlers(self):
        message_handlers.register_handlers(self.bot, settings.commands_list, settings.kwargs_handlers)
        callback_handlers.register_handlers(self.bot, settings.callbacks_handlers)
        filters.register_filters(self.bot, settings.bot_filters)
        await commands.register_commands(self.bot, settings.commands_list)

    async def set_bot_status(self, status: bool):
        await self.bot.set_my_short_description(messages.messages.get_status_text(status))

    async def startup_actions(self):
        await self.set_bot_status(True)

    async def stop_actions(self):
        await self.set_bot_status(False)
        await self.db.commit()
