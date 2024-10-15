import abc

from telebot import types

import settings
from app.app_manager import AppManager
from database import models
from menu import urls
from utils import states


class Action(abc.ABC):
    def __init__(self, *args, query: str = '', **kwargs):
        if query:
            self.query_data = urls.extract_query_data(query)
            self.query_init()
        else:
            self.args_init(*args, **kwargs)

    def query_init(self):
        pass

    def args_init(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def do(self, query: types.CallbackQuery):
        raise NotImplementedError

    def get_url(self):
        return urls.encode_url(settings.ActionsUrls(self.__class__).name, self.get_url_params())

    def get_url_params(self) -> dict:
        return {}


class AskAction(Action):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ask_text, self.wrong_text = self.get_asker_text()

    @staticmethod
    def get_asker_text():
        return '', ''

    async def check(self, message: types.Message) -> bool:
        return True

    @abc.abstractmethod
    def extract_data(self, message: types.Message):
        raise NotImplementedError

    async def do(self, query: types.CallbackQuery):
        bot = AppManager.get_bot()
        user_id = query.from_user.id

        await bot.send_message(user_id, self.ask_text)
        await self.set_asker_state(user_id)

    @abc.abstractmethod
    async def process_data(self, user_id, data):
        raise NotImplementedError

    async def message_handler(self, message: types.Message):
        await ([self.wrong_data_handler, self.correct_data_handler][await self.check(message)](message))

    async def wrong_data_handler(self, message: types.Message):
        await AppManager.get_bot().send_message(message.chat.id, self.wrong_text)

    async def correct_data_handler(self, message: types.Message):
        user_id = message.from_user.id

        (await models.UserDataclass.get_user(user_id)).asker_url = None

        await self.process_data(user_id, self.extract_data(message))
        await self.post_actions(message)

    async def post_actions(self, message: types.Message):
        await AppManager.get_menu().return_to_prev_page(message.from_user.id, message.id)

    async def set_asker_state(self, user_id):
        await AppManager.get_bot().set_state(user_id, states.UserStates.ASK)
        (await models.UserDataclass.get_user(user_id)).asker_url = self.get_url()


class ChooseAction(AskAction):
    @abc.abstractmethod
    async def get_list(self) -> list:
        raise NotImplementedError

    @abc.abstractmethod
    def get_item_repr(self, item):
        raise NotImplementedError

    def extract_data(self, message: types.Message):
        return int(message.text.removeprefix('/'))

    async def check(self, message: types.Message) -> bool:
        if not message.text:
            return False
        text = message.text.removeprefix('/')
        if not text.isdecimal():
            return False
        l = len(await self.get_list())
        return 1 <= int(text) <= l

    async def do(self, query: types.CallbackQuery):
        await super().do(query)
        await AppManager.get_bot().send_message(query.from_user.id,
                                                '\n'.join(f'/{i}: {self.get_item_repr(x)}' for i, x in
                                                          enumerate((await self.get_list()), start=1)))
