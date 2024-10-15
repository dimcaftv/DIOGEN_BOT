import abc
from enum import Enum
from typing import Iterable
from urllib.parse import urlparse

from telebot import types

from app.app_manager import AppManager
from database import models
from utils import states, utils
from . import actions, urls


class MenuItem:
    @classmethod
    def empty(cls):
        return cls(' ', None)

    def __init__(self, text: str, action: actions.Action, admin_only=False, visible=True):
        self.text = text
        self.action = action
        self.admin_only = admin_only
        self.visible = visible


class KeyboardLayout:
    def __init__(self, *rows: Iterable[MenuItem] | MenuItem, is_admin=False, row_width=None):
        if row_width is None:
            row_width = len(max(([x for x in rows if isinstance(x, tuple)] or [[1, 2]]), key=len))

        self.ik = types.InlineKeyboardMarkup(row_width=row_width)
        for r in rows:
            if not isinstance(r, Iterable):
                r = r,

            r = [types.InlineKeyboardButton(text=b.text,
                                            callback_data=('-' if b.action is None else b.action.get_url()))
                 for b in r if b.visible and b.admin_only <= is_admin]
            self.ik.add(*r)


class AbsMenuPage(abc.ABC):
    @classmethod
    async def ainit(cls, *args, **kwargs):
        self = cls(*args, **kwargs)
        await self.post_init()
        return self

    def __init__(self, user_id: int, query: str = '', data: dict = None):
        self.user_id = user_id
        self.query_data = urls.extract_query_data(query)
        self.data = data if data else {}

    async def post_init(self):
        pass

    @abc.abstractmethod
    def get_items(self) -> KeyboardLayout:
        raise NotImplementedError

    @abc.abstractmethod
    def get_page_text(self) -> str:
        raise NotImplementedError

    def get_inline_kb(self):
        return self.get_items().ik

    def get_message_kw(self):
        return {'text': self.get_page_text(), 'reply_markup': self.get_inline_kb()}


class Menu:
    def __init__(self, pages: type[Enum], actions: type[Enum]):
        self.pages = pages
        self.actions = actions

    async def go_to_url(self, user_id: int, url: str, data: dict = None):
        page = await self.get_page(user_id, url, data)
        (await models.UserDataclass.get_user(user_id)).page_url = url
        await self.update_to_page(page)

    async def update_to_page(self, page: AbsMenuPage):
        user_id = page.user_id
        await self.set_menu_state(user_id)
        try:
            await self.edit_menu_msg(user_id, **page.get_message_kw())
        except:
            ans = await AppManager.get_bot().send_message(user_id, 'Загрузка...')
            (await models.UserDataclass.get_user(user_id)).menu_msg_id = ans.id
            await self.edit_menu_msg(user_id, **page.get_message_kw())

    async def edit_msg(self, user_id, msg_id, text, reply_markup=None):
        await AppManager.get_bot().edit_message_text(
                chat_id=user_id,
                message_id=msg_id,
                text=text,
                reply_markup=reply_markup
        )

    async def edit_menu_msg(self, user_id, text, reply_markup=None):
        menu_id = (await models.UserDataclass.get_user(user_id)).menu_msg_id
        await self.edit_msg(user_id, menu_id, text, reply_markup)

    async def get_page(self, user_id: int, url: str, data: dict = None) -> AbsMenuPage:
        parse = urlparse(url)
        return await self.get_page_class(parse.path).ainit(user_id, parse.query, data)

    def get_action(self, callback_data: str) -> actions.Action:
        parse = urlparse(callback_data)
        return self.get_action_class(parse.path)(query=parse.query)

    def get_page_class(self, path) -> type[AbsMenuPage]:
        return self.pages[path].value

    def get_action_class(self, path) -> type[actions.Action]:
        return self.actions[path].value

    async def go_to_last_url(self, user_id: int):
        await self.go_to_url(user_id, (await models.UserDataclass.get_user(user_id)).page_url)

    async def return_to_prev_page(self, user_id: int, last_msg_id: int):
        await self.set_menu_state(user_id)
        await utils.delete_all_after_menu(user_id, last_msg_id)

    async def set_menu_state(self, user_id: int):
        await AppManager.get_bot().set_state(user_id, states.UserStates.MENU)
