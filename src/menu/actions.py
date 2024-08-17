import abc
from typing import Callable
from urllib.parse import urlencode

from telebot import custom_filters, types

from app import App
from utils import states, utils


class Action(abc.ABC):
    key: str = ''
    take_params: bool = False

    @abc.abstractmethod
    def do(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def get_url_id(self):
        raise NotImplementedError


class TransferAction(Action):
    key = 'transfer'
    take_params = True

    def __init__(self, base_url: str = 'main', data: dict = None, full_data: str = None):
        if full_data:
            self.url = full_data
        else:
            self.url = base_url + '?' + (urlencode(data) if data else '')

    def get_url_id(self):
        return ':'.join((self.key, self.url))

    def do(self, query: types.CallbackQuery):
        app = App.get()
        app.menu.go_to_url(query.from_user.id, self.url)
        app.db.add_data(query.from_user.id, **{utils.BotDataKeys.PAGE_URL: self.get_url_id()})


class AskAction(Action):
    key = 'ask_action'

    def __init__(self, filter: Callable | custom_filters.SimpleCustomFilter,
                 ask_text: str, wrong_text: str):
        self.filter = filter
        self.ask_text = ask_text
        self.wrong_text = wrong_text

    def check(self, message: types.Message) -> bool:
        if callable(self.filter):
            return self.filter(message)
        return self.filter.check(message)

    @abc.abstractmethod
    def extract_data(self, message: types.Message):
        raise NotImplementedError

    def get_url_id(self):
        return self.key

    def do(self, query: types.CallbackQuery):
        app = App.get()
        app.bot.send_message(query.message.chat.id, self.ask_text)
        app.bot.set_state(query.from_user.id, states.ActionStates.ASK)
        app.db.add_data(query.from_user.id, **{utils.BotDataKeys.ASKER_URL: self.get_url_id()})

    def clear_ask_messages(self, user_id, up_to_msg_id):
        app = App.get()
        menu_id = app.db.get_menu_id(user_id)
        app.bot.delete_messages(user_id, list(range(menu_id + 1, up_to_msg_id + 1)))

    @abc.abstractmethod
    def process_data(self, user_id, data):
        raise NotImplementedError

    def wrong_data_handler(self, message: types.Message):
        App.get().bot.send_message(message.chat.id, self.wrong_text)

    def correct_data_handler(self, message: types.Message):
        app = App.get()
        user_id = message.from_user.id
        self.clear_ask_messages(user_id, message.id)

        self.process_data(message.from_user.id, self.extract_data(message))
        del app.db.get_data(message.from_user.id)[utils.BotDataKeys.ASKER_URL]
        url = app.db.get_page_url(user_id)
        app.menu.go_to_url(user_id, url)


class AddGroupAction(AskAction):
    key = 'add_group'

    def __init__(self):
        super().__init__(
                lambda x: bool(x.text),
                'Введи название новой группы',
                'Бро, это не название'
        )

    def extract_data(self, message: types.Message):
        return message.text

    def process_data(self, user_id, data):
        App.get().db.create_group(user_id, data)


class DeleteGroupAction(AskAction):
    key = 'delete_group'

    def __init__(self):
        super().__init__(
                lambda x: x.text and x.text.isdigit(),
                'Введи номер группы для удаления',
                'Бро, это не номер'
        )

    def extract_data(self, message: types.Message):
        return int(message.text)

    def process_data(self, user_id, data):
        App.get().db.delete_group(user_id, data)
