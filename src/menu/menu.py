import abc
import asyncio
from typing import Iterable
from urllib.parse import parse_qs, urlparse

from telebot import types

from app.app_manager import AppManager
from database import models
from menu import actions
from utils import states, utils


class MenuItem:
    @classmethod
    def empty(cls):
        return cls(' ', None)

    def __init__(self, text: str, action: actions.Action, admin_only=False):
        self.text = text
        self.action = action
        self.admin_only = admin_only


class KeyboardLayout:
    def __init__(self, *rows: Iterable[MenuItem] | MenuItem, is_admin=False, row_width=2):
        self.ik = types.InlineKeyboardMarkup(row_width=row_width)
        for r in rows:
            if not isinstance(r, Iterable):
                r = r,

            r = [types.InlineKeyboardButton(text=b.text,
                                            callback_data=('-' if b.action is None else b.action.get_url()))
                 for b in r if b.admin_only <= is_admin]
            self.ik.add(*r)


class AbsMenuPage(abc.ABC):
    state: states.BotPagesStates = None
    urlpath: str = None

    def __init__(self, user_id: int, query: str, data: dict = None):
        self.user_id = user_id
        self.query_data = self.extract_data(query)
        self.data = data if data else {}
        self.items = self.get_items()

    def extract_data(self, query: str):
        res = {}
        for k, v in parse_qs(query).items():
            if len(v) == 1:
                v = v[0]
                if v.isdigit():
                    v = int(v)
            res[k] = v
        return res

    @abc.abstractmethod
    def get_items(self) -> KeyboardLayout:
        raise NotImplementedError

    @abc.abstractmethod
    def get_page_text(self) -> str:
        raise NotImplementedError

    def get_inline_kb(self):
        return self.items.ik

    def get_message_kw(self):
        return {'text': self.get_page_text(), 'reply_markup': self.get_inline_kb()}


class Menu:
    def __init__(self, pages: list[type[AbsMenuPage]] = None,
                 actions_list: list[type[actions.Action]] = None):
        self.pages = {p.urlpath: p for p in pages} if pages else {}
        self.actions = {a.key: a for a in actions_list} if actions_list else {}

    async def update_to_page(self, page: AbsMenuPage):
        user_id = page.user_id
        await AppManager.get_bot().set_state(user_id, page.state)
        asyncio.create_task(self.edit_menu_msg(user_id, **page.get_message_kw()))

    async def edit_menu_msg(self, user_id, text, reply_markup=None):
        menu_id = await models.UserDataclass.get_by_key(user_id, 'menu_msg_id')
        await self.edit_msg(user_id, menu_id, text, reply_markup)

    async def edit_msg(self, user_id, msg_id, text, reply_markup=None):
        await AppManager.get_bot().edit_message_text(
                chat_id=user_id,
                message_id=msg_id,
                text=text,
                reply_markup=reply_markup
        )

    def get_action(self, callback_data: str) -> actions.Action:
        part = callback_data.partition(':')
        action = self.actions[part[0]]
        if action.take_params and part[2]:
            return action(full_data=part[2])
        return action()

    def get_page_class(self, path):
        return self.pages[path]

    def get_page(self, user_id: int, url: str, data: dict = None):
        parse = urlparse(url)
        return self.get_page_class(parse.path)(user_id, parse.query, data)

    async def go_to_url(self, user_id: int, url: str, data: dict = None):
        page = self.get_page(user_id, url, data)
        await models.UserDataclass.set_by_key(user_id, 'page_url', url)
        await self.update_to_page(page)

    async def go_to_last_url(self, user_id: int):
        await self.go_to_url(user_id, await self.get_last_url(user_id))

    async def get_last_url(self, user_id: int):
        return await models.UserDataclass.get_by_key(user_id, 'page_url')

    async def set_prev_state(self, user_id: int):
        state = self.get_page_class(urlparse(await self.get_last_url(user_id)).path).state
        await AppManager.get_bot().set_state(user_id, state)

    async def return_to_prev_page(self, user_id: int, last_msg_id: int):
        await self.set_prev_state(user_id)
        await utils.delete_all_after_menu(user_id, last_msg_id)
