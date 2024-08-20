import abc
from urllib.parse import urlencode
from uuid import uuid4

from telebot import types

from app import App
from utils import states, utils


class Action(abc.ABC):
    key: str = ''
    take_params: bool = False

    @abc.abstractmethod
    def do(self, query: types.CallbackQuery):
        raise NotImplementedError

    def get_url_params(self):
        return ''

    def get_url(self):
        return self.key + ':' + self.get_url_params()


class TransferAction(Action):
    key = 'transfer'
    take_params = True

    def __init__(self, base_url: str = 'main', data: dict = None, full_data: str = None):
        if full_data:
            self.url = full_data
        else:
            self.url = base_url + '?' + (urlencode(data) if data else '')

    def get_url_params(self):
        return self.url

    def do(self, query: types.CallbackQuery):
        app = App.get()
        app.menu.go_to_url(query.from_user.id, self.url)
        app.db.add_data(query.from_user.id, **{utils.BotDataKeys.PAGE_URL: self.get_url()})


class DeleteGroupAction(Action):
    key = 'delete_group'
    take_params = True

    def __init__(self, full_data):
        self.group_id = int(full_data)

    def do(self, query: types.CallbackQuery):
        app = App.get()
        app.db.delete_group(self.group_id)
        app.menu.go_to_url(query.from_user.id, 'grouplist')

    def get_url_params(self):
        return str(self.group_id)


class AskAction(Action):
    key = 'ask_action'

    def __init__(self, ask_text: str, wrong_text: str):
        self.ask_text = ask_text
        self.wrong_text = wrong_text

    def check(self, message: types.Message) -> bool:
        return True

    @abc.abstractmethod
    def extract_data(self, message: types.Message):
        raise NotImplementedError

    def do(self, query: types.CallbackQuery):
        app = App.get()
        app.bot.send_message(query.message.chat.id, self.ask_text)
        app.bot.set_state(query.from_user.id, states.ActionStates.ASK)
        app.db.add_data(query.from_user.id, **{utils.BotDataKeys.ASKER_URL: self.get_url()})

    def clear_ask_messages(self, user_id, up_to_msg_id):
        app = App.get()
        menu_id = app.db.get_menu_id(user_id)
        app.bot.delete_messages(user_id, list(range(menu_id + 1, up_to_msg_id + 1)))

    def go_to_prev_page(self, user_id):
        app = App.get()
        url = app.db.get_page_url(user_id)
        app.menu.go_to_url(user_id, url)

    @abc.abstractmethod
    def process_data(self, user_id, data):
        raise NotImplementedError

    def wrong_data_handler(self, message: types.Message):
        App.get().bot.send_message(message.chat.id, self.wrong_text)

    def correct_data_handler(self, message: types.Message):
        app = App.get()
        user_id = message.from_user.id
        self.clear_ask_messages(user_id, message.id)

        del app.db.get_data(message.from_user.id)[utils.BotDataKeys.ASKER_URL]
        self.process_data(message.from_user.id, self.extract_data(message))


class CreateGroupAction(AskAction):
    key = 'add_group'

    def __init__(self):
        super().__init__(
                'Введи название новой группы',
                'Бро, это не название'
        )

    def check(self, message: types.Message) -> bool:
        return bool(message.text)

    def extract_data(self, message: types.Message):
        return message.text

    def process_data(self, user_id, data):
        App.get().db.create_group(user_id, data)
        self.go_to_prev_page(user_id)


class CreateInviteAction(AskAction):
    key = 'create_invite'
    take_params = True

    def __init__(self, full_data):
        super().__init__(
                'Введи сколько человек сможет воспользоваться приглашением',
                'Бро, нормальное число плиз'
        )
        self.group_id = int(full_data)

    def get_url_params(self):
        return str(self.group_id)

    def check(self, message: types.Message) -> bool:
        if not (message.text and message.text.isdigit()):
            return False
        return int(message.text) > 0

    def extract_data(self, message: types.Message):
        return int(message.text)

    def process_data(self, user_id, n):
        app = App.get()
        links = app.db.get_raw_data()[utils.BotDataKeys.INVITE_LINKS]

        while (l := uuid4().hex[:6]) in links:
            continue

        links[l] = (self.group_id, n)

        self.go_to_prev_page(user_id)


class JoinGroupAction(AskAction):
    key = 'join_group'

    def __init__(self):
        super().__init__(
                'Введи код приглашения',
                'Паленый код бро'
        )

    def check(self, message: types.Message) -> bool:
        links = App.get().db.get_raw_data()[utils.BotDataKeys.INVITE_LINKS]
        return message.text in links and links[message.text][1] > 0

    def extract_data(self, message: types.Message):
        return message.text

    def process_data(self, user_id, data):
        app = App.get()
        links = App.get().db.get_raw_data()[utils.BotDataKeys.INVITE_LINKS]

        link = links[data]
        group = app.db.get_group(link[0])

        if user_id not in group.users:
            links[data] = (group.id, link[1] - 1)
            if links[data][1] == 0:
                del links[data]
            group.users.append(user_id)

        app.menu.go_to_url(user_id, f'group?group={group.id}')
