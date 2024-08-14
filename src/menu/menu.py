import abc
from typing import Optional
from urllib.parse import parse_qs, urlparse

from telebot import State, util

from app import App
from menu import actions
from utils import filters, states


class MenuItem:
    def __init__(self, text: str, callback_data: str,
                 action,
                 filter: Optional[filters.MenuItemFilter] = None):
        self.text = text
        self.callback_data = callback_data
        self.action = action
        self.filter = filter

    def check(self, user_id):
        if self.filter is None:
            return True
        return self.filter.check(user_id)


class AbsMenuPage(abc.ABC):
    state: states.AbsAdvancedState = None

    def __init__(self, user_id: int, callback_data: str):
        self.user_id = user_id
        self.id, self.data = self.extract_data(callback_data)
        self.items = {i.callback_data: i for i in self.get_items()}

    def extract_data(self, callback_data: str):
        result = urlparse(callback_data)
        return result.path, {k: (v[0] if len(v) == 1 else v) for k, v in parse_qs(result.query).items()}

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
        return util.quick_markup({i.text: {'callback_data': i.callback_data} for i in self.items.values()})

    def get_message_kw(self):
        return {'text': self.get_page_text(), 'reply_markup': self.get_inline_kb()}


class Menu:
    def __init__(self, pages: list[type(AbsMenuPage)] = None):
        self.pages = {p.state.name: p for p in pages} if pages else {}

    def update_to_page(self, page: AbsMenuPage):
        menu_id = App.get().db.get_menu_id(page.user_id)
        App.get().bot.edit_message_text(chat_id=page.user_id,
                                        message_id=menu_id,
                                        **page.get_message_kw())

    def get_from_page(self, user_id):
        return self.get_page_from_state(App.get().db.bot.get_state(user_id),
                                        App.get().db.get_page_callback_data(user_id),
                                        user_id)

    def get_action(self, callback_data: str, user_id: int) -> actions.Action:
        return self.get_from_page(user_id).get_action(callback_data)

    def get_transfer_page(self, callback_data: str, user_id: int):
        return self.get_page_from_state(self.get_from_page(user_id).get_action(callback_data),
                                        callback_data, user_id)

    def get_page_from_state(self, state: State, callback_data: str, user_id: int):
        if isinstance(state, State):
            state = state.name
        return self.pages[state](user_id, callback_data)
