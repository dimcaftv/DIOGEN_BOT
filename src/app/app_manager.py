from typing import TYPE_CHECKING

from utils.singleton import Singleton

if TYPE_CHECKING:
    from telebot.async_telebot import AsyncTeleBot
    from menu.menu import Menu
    from database.database import DatabaseInterface


class AppManager(metaclass=Singleton):
    def __init__(self, app):
        self.app = app

    @classmethod
    def get_bot(cls) -> 'AsyncTeleBot':
        return cls().app.bot

    @classmethod
    def get_menu(cls) -> 'Menu':
        return cls().app.menu

    @classmethod
    def get_db(cls) -> 'DatabaseInterface':
        return cls().app.db
