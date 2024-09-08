import abc
from urllib.parse import urlencode

from telebot import types

import settings
from app.app_manager import AppManager
from database import models
from utils import states, utils
from utils.calendar import Week


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
        AppManager.get_menu().go_to_url(query.from_user.id, self.url)
        u = models.UserModel.get(query.from_user.id)
        u.page_url = self.get_url()
        u.save()


class DeleteGroupAction(Action):
    key = 'delete_group'
    take_params = True

    def __init__(self, full_data):
        self.group_id = int(full_data)

    def do(self, query: types.CallbackQuery):
        models.GroupModel.get(self.group_id).delete()
        AppManager.get_menu().go_to_url(query.from_user.id, 'grouplist')

    def get_url_params(self):
        return str(self.group_id)


class CopyPrevTimetableAction(Action):
    key = 'copy_prev_timetable'
    take_params = True

    def __init__(self, group_id=None, week=None, full_data: str = None):
        if full_data:
            part = full_data.split('&')
            self.group_id = int(part[0])
            self.week = Week.from_str(part[1])
        else:
            self.group_id = group_id
            self.week = week

    def get_url_params(self):
        return str(self.group_id) + '&' + str(self.week)

    def do(self, query: types.CallbackQuery):
        pweek = self.week.prev()
        lessons = []
        for d1, d2 in zip(pweek, self.week):
            models.LessonModel.delete_where(models.LessonModel.date == d2, models.LessonModel.group_id == self.group_id)
            for l in models.LessonModel.select(models.LessonModel.date == d1,
                                               models.LessonModel.group_id == self.group_id).all():
                lessons.append(models.LessonModel(date=d2, group_id=self.group_id, name=l.name))
        AppManager.get_db().session.add_all(lessons)
        AppManager.get_db().commit()


class ViewHomeworkAction(Action):
    key = 'view_homework'
    take_params = True

    def __init__(self, full_data=None):
        self.lesson_id = int(full_data)

    def get_url_params(self):
        return str(self.lesson_id)

    def do(self, query: types.CallbackQuery):
        solutions = [s.msg_id for s in
                     models.SolutionModel.select(models.SolutionModel.lesson_id == self.lesson_id).all()]
        if not solutions:
            return
        bot = AppManager.get_bot()
        bot.copy_messages(query.from_user.id, settings.MEDIA_STORAGE_TG_ID, solutions)


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
        bot = AppManager.get_bot()
        bot.send_message(query.message.chat.id, self.ask_text)
        bot.set_state(query.from_user.id, states.ActionStates.ASK)

        u = models.UserModel.get(query.from_user.id)
        u.asker_url = self.get_url()
        u.save()

    def go_to_prev_page(self, user_id):
        url = models.UserModel.get(user_id).page_url
        AppManager.get_menu().go_to_url(user_id, url)

    @abc.abstractmethod
    def process_data(self, user_id, data):
        raise NotImplementedError

    def wrong_data_handler(self, message: types.Message):
        AppManager.get_bot().send_message(message.chat.id, self.wrong_text)

    def correct_data_handler(self, message: types.Message):
        user_id = message.from_user.id
        utils.delete_all_after_menu(user_id, message.id)

        u = models.UserModel.get(user_id)
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
        invite = models.GroupInviteModel.get(data)
        group = invite.group
        user = models.UserModel.get(user_id)
        if user not in group.members:
            invite.remain_uses -= 1
            if invite.remain_uses == 0:
                invite.delete()
            group.members.append(user)

        AppManager.get_menu().go_to_url(user_id, f'group?group={group.id}')


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


class CreateTimetableAction(AskAction):
    key = 'create_timetable'
    take_params = True

    def __init__(self, group_id=None, week=None, full_data: str = None):
        super().__init__(
                'Введи уроки для каждого дня недели на новой строке через пробел ("-" если нет уроков)',
                'Бро, введи нормальное расписание'
        )
        if full_data:
            part = full_data.split('&')
            self.group_id = int(part[0])
            self.week = Week.from_str(part[1])
        else:
            self.group_id = group_id
            self.week = week

    def get_url_params(self):
        return str(self.group_id) + '&' + str(self.week)

    def check(self, message: types.Message) -> bool:
        part = message.text.split('\n')
        return len(part) == 7 and all(p.strip() for p in part)

    def extract_data(self, message: types.Message):
        return message.text

    def process_data(self, user_id, data):
        timetable = [p.strip().split() for p in data.split('\n')]

        lessons = []
        for d, t in zip(self.week, timetable):
            models.LessonModel.delete_where(models.LessonModel.date == d, models.LessonModel.group_id == self.group_id)
            if t[0] == '-':
                continue
            for l in t:
                lessons.append(models.LessonModel(date=d, group_id=self.group_id, name=l))
        AppManager.get_db().session.add_all(lessons)
        AppManager.get_db().commit()

        self.go_to_prev_page(user_id)


class AddHomeworkAction(AskAction):
    key = 'add_homework'
    take_params = True

    def __init__(self, full_data):
        super().__init__(
                'Отправь сюда сколько можешь сообщений дз и напиши /stop',
                'Сохраненяю...'
        )
        self.lesson_id = int(full_data)

    def get_url_params(self):
        return str(self.lesson_id)

    def check(self, message: types.Message) -> bool:
        return message.text not in ['/stop', 'stop']

    def extract_data(self, message: types.Message):
        pass

    def process_data(self, user_id, data):
        pass

    def wrong_data_handler(self, message: types.Message):
        super().wrong_data_handler(message)
        utils.delete_all_after_menu(message.from_user.id, message.id + 1)

        u = models.UserModel.get(message.from_user.id)
        u.asker_url = None

        db = AppManager.get_db()
        db.session.add(u)
        db.commit()

        self.go_to_prev_page(message.from_user.id)

    def correct_data_handler(self, message: types.Message):
        solution = AppManager.get_bot().copy_message(settings.MEDIA_STORAGE_TG_ID, message.from_user.id,
                                                     message.id).message_id
        AppManager.get_db().session.add(models.SolutionModel(lesson_id=self.lesson_id, msg_id=solution))
