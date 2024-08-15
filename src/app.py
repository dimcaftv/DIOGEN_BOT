from typing import Self

from telebot import TeleBot, types

from utils.utils import Singleton


class App(metaclass=Singleton):
    @classmethod
    def start(cls, bot: TeleBot):
        return cls(bot)

    @classmethod
    def get(cls) -> Self:
        return cls()

    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.menu = None
        self.db = None

    def set_menu(self, menu):
        self.menu = menu

    def set_db(self, db):
        self.db = db

    def process_query(self, query: types.CallbackQuery):
        data, user_id = query.data, query.from_user.id
        action = self.menu.get_action(user_id, data)
        action.do(query)
