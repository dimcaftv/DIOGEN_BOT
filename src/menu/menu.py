import abc
from typing import Optional
from urllib.parse import parse_qs, urlparse

from telebot import util

from app import App
from menu import actions
from utils import filters, states


class MenuItem:
    def __init__(self, text: str, action,
                 filter: Optional[filters.MenuItemFilter] = None):
        self.text = text
        self.action = action
        self.filter = filter

    def check(self, user_id):
        if self.filter is None:
            return True
        return self.filter.check(user_id)


class AbsMenuPage(abc.ABC):
    state: states.AbsAdvancedState = None
    urlpath: str = None

    def __init__(self, user_id: int, query: str, data: dict = None):
        self.user_id = user_id
        self.query_data = self.extract_data(query)
        self.data = data if data else {}
        self.items = {f'button_{i}': v for i, v in enumerate(self.get_items())}

    def extract_data(self, query: str):
        res = {}
        for k, v in parse_qs(query).items():
            if len(v) == 1:
                v = v[0]
                if v.isdigit():
                    v = int(v)
            res[k] = v
        return res

    def get_action(self, callback_data: str):
        return self.get_item_from_data(callback_data).action

    def get_item_from_data(self, callback_data) -> MenuItem:
        return self.items[callback_data]

    @abc.abstractmethod
    def get_items(self) -> list[MenuItem]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_page_text(self) -> str:
        raise NotImplementedError

    def get_inline_kb(self):
        return util.quick_markup({v.text: {'callback_data': k} for k, v in self.items.items()})

    def get_message_kw(self):
        return {'text': self.get_page_text(), 'reply_markup': self.get_inline_kb()}


class Menu:
    def __init__(self, pages: list[type(AbsMenuPage)] = None):
        self.pages = {p.urlpath: p for p in pages} if pages else {}

    def update_to_page(self, page: AbsMenuPage):
        app = App.get()
        menu_id = app.db.get_menu_id(page.user_id)
        app.bot.set_state(page.user_id, page.state)
        app.bot.edit_message_text(chat_id=page.user_id,
                                  message_id=menu_id,
                                  **page.get_message_kw())

    def get_from_page(self, user_id):
        return self.get_page(user_id, App.get().db.get_page_url(user_id))

    def get_action(self, user_id: int, callback_data: str) -> actions.Action:
        return self.get_from_page(user_id).get_action(callback_data)

    def get_page(self, user_id: int, url: str, data: dict = None):
        parse = urlparse(url)
        return self.pages[parse.path](user_id, parse.query, data)

    def go_to_url(self, user_id: int, url: str, data: dict = None):
        page = self.get_page(user_id, url, data)
        self.update_to_page(page)
