from telebot import State, types, util


class MenuItem:
    def __init__(self, text: str, callback_data: str, transfer_state: State):
        self.text = text
        self.callback_data = callback_data
        self.transfer_state = transfer_state


class MenuPage:
    def __init__(self, state: State, items: list[MenuItem] = None):
        self.state = state
        self.items = {i.callback_data: i for i in items} if items else {}

    def get_transfer_state(self, callback_data: str):
        return self.get_item_from_data(callback_data).transfer_state

    def get_item_from_data(self, callback_data):
        return self.items[callback_data]

    def get_page_text(self):
        return str(self.state.name)

    def get_inline_kb(self):
        return util.quick_markup({i.text: {'callback_data': i.callback_data} for i in self.items.values()})


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
