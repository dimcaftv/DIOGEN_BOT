import abc

from telebot import types

from app.app_manager import AppManager
from database import models
from utils import states


class Action(abc.ABC):
    key: str = ''
    take_params: bool = False

    @abc.abstractmethod
    async def do(self, query: types.CallbackQuery):
        raise NotImplementedError

    def get_url_params(self):
        return ''

    def get_url(self):
        return self.key + ':' + self.get_url_params()


class AskAction(Action):
    key = 'ask_action'

    def __init__(self, ask_text: str, wrong_text: str):
        self.ask_text = ask_text
        self.wrong_text = wrong_text

    async def check(self, message: types.Message) -> bool:
        return True

    @abc.abstractmethod
    def extract_data(self, message: types.Message):
        raise NotImplementedError

    async def do(self, query: types.CallbackQuery):
        bot = AppManager.get_bot()
        await bot.send_message(query.message.chat.id, self.ask_text)

        await bot.set_state(query.from_user.id, states.ActionStates.ASK)
        await models.UserDataclass.set_by_key(query.from_user.id, 'asker_url', self.get_url())

    @abc.abstractmethod
    async def process_data(self, user_id, data):
        raise NotImplementedError

    async def message_handler(self, message: types.Message):
        await ([self.wrong_data_handler, self.correct_data_handler][await self.check(message)](message))

    async def wrong_data_handler(self, message: types.Message):
        await AppManager.get_bot().send_message(message.chat.id, self.wrong_text)

    async def correct_data_handler(self, message: types.Message):
        user_id = message.from_user.id

        await models.UserDataclass.set_by_key(user_id, 'asker_url', None)

        await self.process_data(user_id, self.extract_data(message))
        await self.post_actions(user_id, message)

    async def post_actions(self, user_id, message: types.Message):
        await AppManager.get_menu().return_to_prev_page(user_id, message.id)
