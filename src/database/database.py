from telebot import TeleBot

from utils import utils


class SimpleBotStateStorage(metaclass=utils.Singleton):
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.bot.enable_saving_states('../.state-save/states.pkl')

    def set_default_state(self, user_id, chat_id=None):
        self.bot.set_state(user_id, None, chat_id)

    def add_data(self, user_id, chat_id=None, **kwargs):
        self.bot.add_data(user_id, chat_id, **kwargs)

    def get_data(self, user_id, chat_id=None) -> dict:
        if chat_id is None:
            chat_id = user_id
        return self.bot.current_states.get_data(chat_id, user_id)

    def __del__(self):
        self.bot.current_states.update_data()
        print('saved')
