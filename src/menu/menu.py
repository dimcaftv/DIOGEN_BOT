from typing import Optional

from telebot import State, util

from utils import filters, states


class MenuItem:
    def __init__(self, text: str, callback_data: str, transfer_state: State,
                 filter: Optional[filters.MenuItemFilter] = None):
        self.text = text
        self.callback_data = callback_data
        self.transfer_state = transfer_state
        self.filter = filter

    def check(self, user_id):
        if self.filter is None:
            return True
        return self.filter.check(user_id)


class MenuPage:
    def __init__(self, state: states.AbsAdvancedState, items: list[MenuItem] = None):
        self.state = state
        self.items = {i.callback_data: i for i in items} if items else {}

    def get_transfer_state(self, callback_data: str):
        return self.get_item_from_data(callback_data).transfer_state

    def get_item_from_data(self, callback_data):
        return self.items[callback_data]

    def get_items_for_user(self, user_id):
        return [i for i in self.items.values() if i.check(user_id)]

    def get_page_text(self, user_id):
        return self.state.get_message_text(user_id)

    def get_inline_kb(self, user_id):
        return util.quick_markup({i.text: {'callback_data': i.callback_data} for i in self.get_items_for_user(user_id)})

    def get_message_kw(self, user_id):
        return {'text': self.get_page_text(user_id), 'reply_markup': self.get_inline_kb(user_id)}


class Menu:
    def __init__(self, pages: list[MenuPage] = None):
        self.pages = {p.state.name: p for p in pages} if pages else {}

    def get_transfer_state(self, state: State, callback_data: str):
        return self.get_page_from_state(state).get_transfer_state(callback_data)

    def get_page_from_state(self, state: State):
        if isinstance(state, State):
            return self.pages[state.name]
        elif isinstance(state, str):
            return self.pages[state]
