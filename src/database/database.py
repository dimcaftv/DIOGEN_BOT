import dataclasses

from telebot import TeleBot

from utils import utils


@dataclasses.dataclass
class Group:
    id: int
    name: str
    admin: int
    users: list[int] = dataclasses.field(default_factory=list)


class SimpleBotStateStorage(metaclass=utils.Singleton):
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.bot.enable_saving_states('../.state-save/states.pkl')
        self.get_raw_data().setdefault(utils.BotDataKeys.GROUPS, [])
        self.askers = {}

    def set_default_state(self, user_id, chat_id=None):
        self.bot.set_state(user_id, None, chat_id)

    def add_data(self, user_id, chat_id=None, **kwargs):
        self.bot.add_data(user_id, chat_id, **kwargs)

    def get_data(self, user_id, chat_id=None) -> dict:
        if chat_id is None:
            chat_id = user_id
        return self.bot.current_states.get_data(chat_id, user_id)

    def get_raw_data(self):
        return self.bot.current_states.data

    def get_user_groups(self, user_id):
        groups: list[Group] = []
        for g in self.get_raw_data()[utils.BotDataKeys.GROUPS]:
            if user_id in g.users:
                groups.append(g)
        return groups

    def create_group(self, user_id, name):
        groups = self.get_raw_data()[utils.BotDataKeys.GROUPS]
        i = groups[-1].id + 1 if groups else 1
        groups.append(Group(i, name, user_id, [user_id]))

    def get_page_callback_data(self, user_id):
        return self.get_data(user_id).setdefault(utils.BotDataKeys.PAGE_CB_DATA, '')

    def set_asker(self, user_id, asker):
        self.askers[user_id] = asker

    def get_asker(self, user_id):
        return self.askers.get(user_id)

    def get_menu_id(self, user_id):
        return self.get_data(user_id).get(utils.BotDataKeys.MENU_MSG_ID)

    def __del__(self):
        self.bot.current_states.update_data()
        print('saved')
