import abc
from urllib.parse import urlencode

from telebot import types

from app import App
from database import models
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
        u = models.UserModel.get(query.from_user.id)
        u.page_url = self.get_url()
        u.save()


class DeleteGroupAction(Action):
    key = 'delete_group'
    take_params = True

    def __init__(self, full_data):
        self.group_id = int(full_data)

    def do(self, query: types.CallbackQuery):
        app = App.get()
        models.GroupModel.get(self.group_id).delete()
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

        u = models.UserModel.get(query.from_user.id)
        u.asker_url = self.get_url()
        u.save()

    def clear_ask_messages(self, user_id, up_to_msg_id):
        app = App.get()
        menu_id = models.UserModel.get(user_id).menu_msg_id
        app.bot.delete_messages(user_id, list(range(menu_id + 1, up_to_msg_id + 1)))

    def go_to_prev_page(self, user_id):
        app = App.get()
        url = models.UserModel.get(user_id).page_url
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

        u = models.UserModel.get(message.from_user.id)
        u.asker_url = None
        u.save()

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
        u = models.UserModel.get(user_id)
        models.GroupModel(name=data, admin=u, members=[u]).save()

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
        models.GroupInviteModel(link=utils.generate_invite_link(), group_id=self.group_id, remain_uses=n).save()

        self.go_to_prev_page(user_id)


class JoinGroupAction(AskAction):
    key = 'join_group'

    def __init__(self):
        super().__init__(
                'Введи код приглашения',
                'Паленый код бро'
        )

    def check(self, message: types.Message) -> bool:
        l = message.text.lower()
        invite = models.GroupInviteModel.get(l)
        return bool(invite) and invite.remain_uses > 0

    def extract_data(self, message: types.Message):
        return message.text.lower()

    def process_data(self, user_id, data):
        app = App.get()
        invite = models.GroupInviteModel.get(data)
        group = invite.group
        user = models.UserModel.get(user_id)
        if user not in group.members:
            invite.remain_uses -= 1
            if invite.remain_uses == 0:
                invite.delete()
            group.members.append(user)

        app.menu.go_to_url(user_id, f'group?group={group.id}')


class KickUserAction(AskAction):
    key = 'kick_user'
    take_params = True

    def __init__(self, full_data):
        super().__init__(
                'Введи ник участника',
                'Бро, введи нормальный ник'
        )
        self.group_id = int(full_data)

    def get_url_params(self):
        return str(self.group_id)

    def extract_data(self, message: types.Message):
        return message.text

    def check(self, message: types.Message) -> bool:
        users = models.GroupModel.get(self.group_id).members
        return (message.text != message.from_user.first_name and
                message.text in [utils.get_tg_user_from_model(u).first_name for u in users])

    def process_data(self, user_id, data):
        group = models.GroupModel.get(self.group_id)

        u = 0
        for u in group.members:
            if utils.get_tg_user_from_model(u).first_name == data:
                break

        group.members.remove(u)

        self.go_to_prev_page(user_id)
