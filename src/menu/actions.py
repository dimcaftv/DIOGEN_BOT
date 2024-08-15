import abc
from enum import Enum
from typing import Callable
from urllib.parse import urlencode

from telebot import custom_filters, types

from app import App
from utils import states, utils


class Action(abc.ABC):
    @abc.abstractmethod
    def do(self, *args, **kwargs):
        raise NotImplementedError


class TransferAction(Action):
    def __init__(self, base_url: str, data: dict = None):
        self.url = base_url + '?' + (urlencode(data) if data else '')

    def do(self, query: types.CallbackQuery):
        app = App.get()
        app.menu.go_to_url(query.from_user.id, self.url)
        app.db.add_data(query.from_user.id, **{utils.BotDataKeys.PAGE_URL: self.url})


class AskAction(Action):
    def __init__(self, filter: Callable | custom_filters.SimpleCustomFilter,
                 ask_text: str, wrong_text: str):
        self.filter = filter
        self.ask_text = ask_text
        self.wrong_text = wrong_text

    def check(self, message: types.Message) -> bool:
        if callable(self.filter):
            return self.filter(message)
        return self.filter.check(message)

    def do(self, query: types.CallbackQuery):
        app = App.get()
        app.bot.send_message(query.message.chat.id, self.ask_text)
        app.bot.set_state(query.from_user.id, states.ActionStates.ASK)
        App.get().db.set_asker(query.from_user.id, self)

    def set_answer_data(self, message: types.Message):
        app = App.get()
        user_id = message.from_user.id
        menu_id = app.db.get_menu_id(user_id)

        app.bot.delete_messages(message.chat.id, list(range(menu_id + 1, message.id + 1)))

        url = app.db.get_page_url(user_id)
        app.menu.go_to_url(user_id, url, {'ask_data': message.text})


class ActionsEnum(Enum):
    TRANSFER = TransferAction
    ASK = AskAction
