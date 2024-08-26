import abc
from urllib.parse import parse_qs, urlparse

from telebot import util

from app.app_manager import AppManager
from database import models
from menu import actions
from utils import states, utils


class MenuItem:
    def __init__(self, text: str, action: actions.Action):
        self.text = text
        self.action = action


class AbsMenuPage(abc.ABC):
    state: states.AbsAdvancedState = None
    urlpath: str = None

    def __init__(self, user_id: int, query: str, data: dict = None):
        self.user = models.UserModel.get(user_id)
        self.tg_user = utils.get_tg_user_from_model(self.user)
        self.query_data = self.extract_data(query)
        self.data = data if data else {}
        self.items = {v.action.get_url(): v for v in self.get_items()}

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
    def __init__(self, pages: list[type[AbsMenuPage]] = None,
                 actions_list: list[type[actions.Action]] = None):
        self.pages = {p.urlpath: p for p in pages} if pages else {}
        self.actions = {a.key: a for a in actions_list} if actions_list else {}

    def update_to_page(self, page: AbsMenuPage):
        bot = AppManager.get_bot()
        menu_id = page.user.menu_msg_id
        bot.set_state(page.user.id, page.state)
        bot.edit_message_text(chat_id=page.user.id,
                                  message_id=menu_id,
                                  **page.get_message_kw())

    def get_action(self, callback_data: str) -> actions.Action:
        part = callback_data.partition(':')
        action = self.actions[part[0]]
        if action.take_params and part[2]:
            return action(full_data=part[2])
        return action()

    def get_page(self, user_id: int, url: str, data: dict = None):
        parse = urlparse(url)
        return self.pages[parse.path](user_id, parse.query, data)

    def go_to_url(self, user_id: int, url: str, data: dict = None):
        page = self.get_page(user_id, url, data)
        self.update_to_page(page)
