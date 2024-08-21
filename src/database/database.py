import dataclasses
from uuid import uuid4

from telebot import TeleBot

from app import App
from utils import singleton, utils


@dataclasses.dataclass
class Group:
    id: int
    name: str
    admin: int
    users: list[int] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class GroupInvite:
    id: str
    group_id: int
    remain_uses: int

    @classmethod
    def generate_invite(cls, group_id, remain):
        invites = App.get().db.get_raw_data()[utils.BotDataKeys.INVITE_LINKS]
        i = cls(cls.generate_id(), group_id, remain)
        invites[i.id] = i

    @staticmethod
    def generate_id():
        invites = App.get().db.get_raw_data()[utils.BotDataKeys.INVITE_LINKS]

        while (l := uuid4().hex[:6]) in invites:
            continue
        return l


class SimpleBotStateStorage(metaclass=singleton.Singleton):
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.bot.enable_saving_states('../.state-save/states.pkl')
        self.get_raw_data().setdefault(utils.BotDataKeys.GROUPS, {})
        self.get_raw_data().setdefault(utils.BotDataKeys.INVITE_LINKS, {})

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

    def get_user_groups(self, user_id) -> list[Group]:
        groups: list[Group] = []
        for g in self.get_raw_data()[utils.BotDataKeys.GROUPS].values():
            if user_id in g.users:
                groups.append(g)
        return groups

    def get_group(self, group_id) -> Group:
        return self.get_raw_data()[utils.BotDataKeys.GROUPS][group_id]

    def create_group(self, user_id, name):
        groups = self.get_raw_data()[utils.BotDataKeys.GROUPS]
        i = groups[sorted(groups.keys())[-1]].id + 1 if groups else 1
        groups[i] = Group(i, name, user_id, [user_id])

    def delete_group(self, group_id):
        del self.get_raw_data()[utils.BotDataKeys.GROUPS][group_id]

    def get_page_url(self, user_id):
        return self.get_data(user_id).setdefault(utils.BotDataKeys.PAGE_URL, 'main')

    def get_menu_id(self, user_id):
        return self.get_data(user_id).get(utils.BotDataKeys.MENU_MSG_ID)

    def __del__(self):
        self.bot.current_states.update_data()
        print('saved')


def set_app_db(bot: TeleBot):
    App.get().set_db(SimpleBotStateStorage(bot))
