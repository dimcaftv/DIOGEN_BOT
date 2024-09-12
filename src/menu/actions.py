import abc
from datetime import date
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


class DeleteGroupAction(Action):
    key = 'delete_group'
    take_params = True

    def __init__(self, full_data):
        self.group_id = int(full_data)

    def do(self, query: types.CallbackQuery):
        with AppManager.get_db().cnt_mng as s:
            g = models.GroupModel.get(self.group_id, session=s)
            s.delete(g)
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
        with AppManager.get_db().cnt_mng as s:
            for d1, d2 in zip(pweek, self.week):
                models.LessonModel.delete_where(models.LessonModel.date == d2,
                                                models.LessonModel.group_id == self.group_id, session=s)
                for l in models.LessonModel.select(models.LessonModel.date == d1,
                                                   models.LessonModel.group_id == self.group_id).all():
                    lessons.append(models.LessonModel(date=d2, group_id=self.group_id, name=l.name))
            s.add_all(lessons)


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
        bot = AppManager.get_bot()
        if not solutions:
            bot.answer_callback_query(query.id, 'На этот урок ничего нет', True)
            return
        bot.copy_messages(query.from_user.id, settings.MEDIA_STORAGE_TG_ID, solutions)
        bot.send_message(query.from_user.id, 'Назад - /back')


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

    @abc.abstractmethod
    def process_data(self, user_id, data):
        raise NotImplementedError

    def message_handler(self, message: types.Message):
        funcs = [self.wrong_data_handler, self.correct_data_handler]
        funcs[self.check(message)](message)

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
        with AppManager.get_db().cnt_mng as s:
            u = models.UserModel.get(user_id, session=s)
            g = models.GroupModel(name=data, admin=u, members=[u])
            if len(u.groups) == 1:
                u.fav_group_id = g.id
            s.add_all([g, u])
        AppManager.get_menu().go_to_last_url(user_id)


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
        with AppManager.get_db().cnt_mng as s:
            s.add(models.GroupInviteModel(link=utils.generate_invite_link(), group_id=self.group_id, remain_uses=n))

        AppManager.get_menu().set_prev_state(user_id)


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
        with AppManager.get_db().cnt_mng as s:
            invite = models.GroupInviteModel.get(data, session=s)
            user = models.UserModel.get(user_id, session=s)
            group = invite.group
            if user not in group.members:
                invite.remain_uses -= 1
                if invite.remain_uses == 0:
                    s.delete(invite)
                group.members.append(user)
                if len(user.groups) == 1:
                    user.fav_group_id = group.id
            gid = group.id

        AppManager.get_menu().go_to_url(user_id, f'group?group={gid}')


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
        return (message.text != message.from_user.username and
                message.text in [u.username for u in users])

    def process_data(self, user_id, data):
        with AppManager.get_db().cnt_mng as s:
            group = models.GroupModel.get(self.group_id, session=s)
            u = models.UserModel.select(models.UserModel.username == data, session=s).first()
            group.members.remove(u)

        AppManager.get_menu().set_prev_state(user_id)


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
        with AppManager.get_db().cnt_mng as s:
            for d, t in zip(self.week, timetable):
                models.LessonModel.delete_where(models.LessonModel.date == d,
                                                models.LessonModel.group_id == self.group_id, session=s)
                if t[0] == '-':
                    continue
                for l in t:
                    lessons.append(models.LessonModel(date=d, group_id=self.group_id, name=l))
            s.add_all(lessons)

        AppManager.get_menu().set_prev_state(user_id)


class AddHomeworkAction(AskAction):
    key = 'add_homework'
    take_params = True

    def __init__(self, full_data):
        super().__init__(
                'Отправь сюда сколько можешь сообщений дз и напиши /stop\nТолько не скидывай несколько фотографий одним сообщением, я еще это не пофиксил',
                'Сохраняю...'
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
        with AppManager.get_db().cnt_mng as s:
            u = models.UserModel.get(message.from_user.id, session=s)
            u.asker_url = None

        AppManager.get_menu().set_prev_state(message.from_user.id)

    def correct_data_handler(self, message: types.Message):
        solution = AppManager.get_bot().copy_message(settings.MEDIA_STORAGE_TG_ID,
                                                     message.from_user.id,
                                                     message.id).message_id
        with AppManager.get_db().cnt_mng as s:
            s.add(models.SolutionModel(lesson_id=self.lesson_id, msg_id=solution,
                                       author_id=message.from_user.id, created=date.today()))
