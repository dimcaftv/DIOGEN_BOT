from datetime import date

from telebot import types

import settings
from app.app_manager import AppManager
from database import models
from menu.actions import AskAction
from messages import messages
from utils import utils
from utils.calendar import Week


class CreateGroupAction(AskAction):
    key = 'add_group'

    def __init__(self):
        super().__init__(
                'Введи название новой группы',
                'Бро, это не название'
        )

    async def check(self, message: types.Message) -> bool:
        return bool(message.text)

    def extract_data(self, message: types.Message):
        return message.text

    async def process_data(self, user_id, data):
        async with AppManager.get_db().cnt_mng as s:
            u = await models.UserModel.get(user_id, session=s)
            g = models.GroupModel(name=data)
            sets = models.GroupSettings(group=g)
            s.add_all([g, u, sets])
            g.admin = u
            g.members.append(u)
            if len(u.groups) == 1:
                u.fav_group_id = g.id

    async def post_actions(self, user_id, message: types.Message):
        await utils.delete_all_after_menu(user_id, message.id)
        await AppManager.get_menu().go_to_last_url(user_id)


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

    async def check(self, message: types.Message) -> bool:
        if not (message.text and message.text.isdecimal()):
            return False
        return int(message.text) > 0

    def extract_data(self, message: types.Message):
        return int(message.text)

    async def process_data(self, user_id, n):
        async with AppManager.get_db().cnt_mng as s:
            s.add(models.GroupInviteModel(link=(await utils.generate_invite_link()), group_id=self.group_id,
                                          remain_uses=n))


class JoinGroupAction(AskAction):
    key = 'join_group'

    def __init__(self):
        super().__init__(
                'Введи код приглашения',
                'Паленый код бро'
        )

    async def check(self, message: types.Message) -> bool:
        l = message.text.lower()
        invite = await models.GroupInviteModel.get(l)
        return bool(invite) and invite.remain_uses > 0

    def extract_data(self, message: types.Message):
        return message.text.lower()

    async def process_data(self, user_id, data):
        async with AppManager.get_db().cnt_mng as s:
            invite = await models.GroupInviteModel.get(data, session=s)
            user = await models.UserModel.get(user_id, session=s)
            group = invite.group
            if user not in group.members:
                invite.remain_uses -= 1
                if invite.remain_uses == 0:
                    await s.delete(invite)
                group.members.append(user)
                if len(user.groups) == 1:
                    user.fav_group_id = group.id
            self.join_group_id = group.id

    async def post_actions(self, user_id, message: types.Message):
        await AppManager.get_menu().go_to_url(user_id, f'group?group={self.join_group_id}')
        await utils.delete_all_after_menu(user_id, message.id)


class KickUserAction(AskAction):
    key = 'kick_user'
    take_params = True

    def __init__(self, full_data):
        super().__init__(
                'Введи номер участника',
                'Бро, введи нормальный ник'
        )
        self.group_id = int(full_data)

    def get_url_params(self):
        return str(self.group_id)

    def extract_data(self, message: types.Message):
        return int(message.text.removeprefix('/'))

    async def check(self, message: types.Message) -> bool:
        text = message.text.removeprefix('/')
        if not text.isdecimal():
            return False
        users = len((await models.GroupModel.get(self.group_id)).members)
        return 1 <= int(text) <= users

    async def do(self, query: types.CallbackQuery):
        await super().do(query)
        members = (await models.GroupModel.get(self.group_id)).members
        await AppManager.get_menu().edit_menu_msg(query.from_user.id,
                                                  '\n'.join(f'/{i}: {(u.username or str(u.id))}' for i, u in
                                                            enumerate(members, start=1)))

    async def process_data(self, user_id, data):
        async with AppManager.get_db().cnt_mng as s:
            group = await models.GroupModel.get(self.group_id, session=s)
            u = group.members.pop(data - 1)
            if not group.members:
                await s.delete(group)
                await models.UserDataclass.set_by_key(user_id, 'page_url', 'grouplist')
                return
            if u.id == user_id:
                from random import choice
                group.admin = choice(group.members)

    async def post_actions(self, user_id, message: types.Message):
        await AppManager.get_menu().go_to_last_url(user_id)
        await utils.delete_all_after_menu(user_id, message.id)


class CreateTimetableAction(AskAction):
    key = 'create_timetable'
    take_params = True

    def __init__(self, group_id=None, week=None, full_data: str = None):
        super().__init__(
                'Введи уроки для каждого дня недели на новой строке через пробел ("-" если нет уроков)',
                'Бро, введи нормальное расписание'
        )
        self.group_id = group_id
        self.week = week
        if full_data:
            part = full_data.split('&')
            self.group_id = int(part[0])
            self.week = Week.from_str(part[1])

    def get_url_params(self):
        return str(self.group_id) + '&' + str(self.week)

    async def check(self, message: types.Message) -> bool:
        part = message.text.split('\n')
        return len(part) == 7 and all(p.strip() for p in part)

    def extract_data(self, message: types.Message):
        return message.text

    async def process_data(self, user_id, data):
        timetable = [p.strip().split() for p in data.split('\n')]

        lessons = []
        async with AppManager.get_db().cnt_mng as s:
            for d, t in zip(self.week, timetable):
                await models.LessonModel.delete_where(models.LessonModel.date == d,
                                                      models.LessonModel.group_id == self.group_id, session=s)
                if t[0] == '-':
                    continue
                for l in t:
                    lessons.append(models.LessonModel(date=d, group_id=self.group_id, name=l))
            s.add_all(lessons)


class AddHomeworkAction(AskAction):
    key = 'add_homework'
    take_params = True

    def __init__(self, full_data):
        super().__init__(
                'Отправь сюда сколько можешь сообщений дз и напиши /stop\nЕсли отправляешь много фоток за раз, то проверь, что все дошли.',
                'Сохраняю...'
        )
        self.lesson_id = int(full_data)

    def get_url_params(self):
        return str(self.lesson_id)

    async def check(self, message: types.Message) -> bool:
        return message.text not in ['/stop', 'stop']

    def extract_data(self, message: types.Message):
        pass

    async def process_data(self, user_id, data):
        pass

    async def wrong_data_handler(self, message: types.Message):
        user_id = message.from_user.id

        await models.UserDataclass.set_by_key(user_id, 'asker_url', None)
        await AppManager.get_menu().return_to_prev_page(user_id, message.id)

        lesson = await models.LessonModel.get(self.lesson_id)
        settings = (await models.GroupModel.get(lesson.group_id)).settings
        if settings.general_group_chat_id and settings.new_answer_notify:
            await AppManager.get_bot().send_message(settings.general_group_chat_id,
                                                    (
                                                            settings.answer_notify_template or messages.default_notify_template)
                                                    .format(lesson_name=lesson.name,
                                                            date=Week.standart_day_format(lesson.date)))

    async def correct_data_handler(self, message: types.Message):
        solution = await AppManager.get_bot().copy_message(settings.MEDIA_STORAGE_TG_ID,
                                                           message.from_user.id,
                                                           message.id)
        file_id = None
        if message.photo:
            file_id = message.photo[-1].file_id
        async with AppManager.get_db().cnt_mng as s:
            s.add(models.SolutionModel(lesson_id=self.lesson_id, msg_id=solution.message_id,
                                       author_id=message.from_user.id, created=date.today(),
                                       file_id=file_id))


class ChangeGroupAdminAction(AskAction):
    key = 'change_group_admin'
    take_params = True

    def __init__(self, full_data):
        super().__init__(
                'Введи номер участника, которому передашь админку',
                'Этот номер не подходит'
        )

        self.group_id = int(full_data)

    def get_url_params(self):
        return str(self.group_id)

    def extract_data(self, message: types.Message):
        return int(message.text.removeprefix('/'))

    async def check(self, message: types.Message) -> bool:
        text = message.text.removeprefix('/')
        if not text.isdecimal():
            return False
        users = len((await models.GroupModel.get(self.group_id)).members)
        return 1 <= int(text) <= users

    async def do(self, query: types.CallbackQuery):
        await super().do(query)
        members = (await models.GroupModel.get(self.group_id)).members
        await AppManager.get_menu().edit_menu_msg(query.from_user.id,
                                                  '\n'.join(f'/{i}: {(u.username or str(u.id))}' for i, u in
                                                            enumerate(members, start=1)))

    async def process_data(self, user_id, data):
        async with AppManager.get_db().cnt_mng as s:
            group = await models.GroupModel.get(self.group_id, session=s)
            group.admin = group.members[data - 1]

    async def post_actions(self, user_id, message: types.Message):
        await utils.delete_all_after_menu(user_id, message.id)
        await AppManager.get_menu().go_to_url(user_id, f'group?group={self.group_id}')


class ChangeNotifyTemplateAction(AskAction):
    key = 'change_notify_template'
    take_params = True

    def __init__(self, full_data):
        super().__init__(
                'Введи шаблон для сообщения, отправляемого при добавлении нового ответа в бота. В шаблоне можно использовать динамические параметры:\n'
                '{lesson_name} - название урока\n'
                '{date} - дата урока',
                'чет не то'
        )

        self.group_id = int(full_data)

    def get_url_params(self):
        return str(self.group_id)

    def extract_data(self, message: types.Message):
        return message.text

    async def check(self, message: types.Message) -> bool:
        return bool(message.text)

    async def process_data(self, user_id, data):
        async with AppManager.get_db().cnt_mng as s:
            settings = await models.GroupSettings.get(self.group_id, session=s)
            settings.answer_notify_template = data
