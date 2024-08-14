import abc
from enum import Enum
from typing import Callable
from urllib.parse import parse_qs, urlencode, urlparse

from telebot import State, custom_filters, types

from app import App
from utils import states, utils


class Action(abc.ABC):
    @abc.abstractmethod
    def do(self, *args, **kwargs):
        raise NotImplementedError


class TransferAction(Action):
    def __init__(self, transfer_state: State):
        self.transfer_state = transfer_state

    def do(self, query: types.CallbackQuery):
        app = App.get()
        to_page = app.menu.get_page_from_state(self.transfer_state, query.data, query.from_user.id)
        app.bot.set_state(query.from_user.id, to_page.state)
        app.menu.update_to_page(to_page)
        app.db.add_data(query.from_user.id, **{utils.BotDataKeys.PAGE_CB_DATA: query.data})


class AskAction(Action):
    def __init__(self, filter: Callable | custom_filters.SimpleCustomFilter, prev_state: State, ask_text: str,
                 wrong_text: str):
        self.prev_state = prev_state
        self.filter = filter
        self.wrong_text = wrong_text
        self.ask_text = ask_text

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

        app.bot.set_state(message.from_user.id, self.prev_state)
        app.bot.delete_messages(message.chat.id, list(range(menu_id + 1, message.id + 1)))

        parseurl = urlparse(app.db.get_page_callback_data(user_id))
        cb = parseurl.path + '?' + urlencode(dict(**parse_qs(parseurl.query), **{'ask_data': message.text}))

        page = app.menu.get_page_from_state(self.prev_state, cb, user_id)
        app.menu.update_to_page(page)


class ActionsEnum(Enum):
    TRANSFER = TransferAction
    ASK = AskAction
