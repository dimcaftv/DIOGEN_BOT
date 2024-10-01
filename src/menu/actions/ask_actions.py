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
    @staticmethod
    def get_asker_text():
        return ('Введи название новой группы',
                'Бро, это не название')

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

    async def post_actions(self, message: types.Message):
        await utils.delete_all_after_menu(message.from_user.id, message.id)
        await AppManager.get_menu().go_to_last_url(message.from_user.id)


class CreateInviteAction(AskAction):
    @staticmethod
    def get_asker_text():
        return ('Введи сколько человек сможет воспользоваться приглашением',
                'Бро, нормальное число плиз')

    def query_init(self):
        self.group_id = self.query_data['g']

    def args_init(self, group_id):
        self.group_id = group_id

    def get_url_params(self):
        return {'g': self.group_id}

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
    @staticmethod
    def get_asker_text():
        return ('Введи код приглашения',
                'Паленый код бро')

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

    async def post_actions(self, message: types.Message):
        await AppManager.get_menu().go_to_url(message.from_user.id, f'group?group={self.join_group_id}')
        await utils.delete_all_after_menu(message.from_user.id, message.id)


class KickUserAction(AskAction):
    @staticmethod
    def get_asker_text():
        return ('Введи номер участника',
                'Бро, введи нормальный ник')

    def query_init(self):
        self.group_id = self.query_data['g']

    def args_init(self, group_id):
        self.group_id = group_id

    def get_url_params(self):
        return {'g': self.group_id}

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
                (await models.UserDataclass.get_user(user_id)).page_url = 'grouplist'
                return
            if u.id == user_id:
                from random import choice
                group.admin = choice(group.members)

    async def post_actions(self, message: types.Message):
        await AppManager.get_menu().go_to_last_url(message.from_user.id)
        await utils.delete_all_after_menu(message.from_user.id, message.id)


class CreateTimetableAction(AskAction):
    @staticmethod
    def get_asker_text():
        return ('Введи уроки для каждого дня недели на новой строке через пробел ("-" если нет уроков)',
                'Бро, введи нормальное расписание')

    def query_init(self):
        self.group_id = self.query_data['g']
        self.week = Week.from_str(self.query_data['w'])

    def args_init(self, group_id, week):
        self.group_id = group_id
        self.week = week

    def get_url_params(self):
        return {'g': self.group_id, 'w': self.week}

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
    @staticmethod
    def get_asker_text():
        return (
            'Отправь сюда сколько можешь сообщений дз и напиши /stop\nЕсли отправляешь много фоток за раз, то проверь, что все дошли.',
            'Сохраняю...')

    def query_init(self):
        self.lesson_id = self.query_data['l']

    def args_init(self, lesson_id):
        self.lesson_id = lesson_id

    def get_url_params(self):
        return {'l': self.lesson_id}

    async def check(self, message: types.Message) -> bool:
        return message.text != '/stop'

    def extract_data(self, message: types.Message):
        pass

    async def process_data(self, user_id, data):
        pass

    async def do(self, query: types.CallbackQuery):
        await super().do(query)
        (await models.UserDataclass.get_user(query.from_user.id)).sent_hw = False

    async def wrong_data_handler(self, message: types.Message):
        user_id = message.from_user.id

        u = await models.UserDataclass.get_user(user_id)
        u.asker_url = None
        await AppManager.get_menu().return_to_prev_page(user_id, message.id)

        lesson = await models.LessonModel.get(self.lesson_id)
        settings = (await models.GroupModel.get(lesson.group_id)).settings
        if u.sent_hw and settings.general_group_chat_id and settings.new_answer_notify:
            await (AppManager.get_bot()
                   .send_message(settings.general_group_chat_id,
                                 (settings.answer_notify_template or messages.default_notify_template)
                                 .format(lesson_name=lesson.name,
                                         date=Week.standart_day_format(lesson.date))))

    async def correct_data_handler(self, message: types.Message):
        user_id = message.from_user.id
        solution = await AppManager.get_bot().copy_message(settings.MEDIA_STORAGE_TG_ID,
                                                           user_id, message.id)
        file_id = None
        if message.photo:
            file_id = message.photo[-1].file_id
        async with AppManager.get_db().cnt_mng as s:
            s.add(models.SolutionModel(lesson_id=self.lesson_id, msg_id=solution.message_id,
                                       author_id=user_id, created=date.today(),
                                       file_id=file_id))
        u = await models.UserDataclass.get_user(user_id)
        if not u.sent_hw:
            u.sent_hw = True


class ChangeGroupAdminAction(AskAction):
    @staticmethod
    def get_asker_text():
        return ('Введи номер участника, которому передашь админку',
                'Этот номер не подходит')

    def query_init(self):
        self.group_id = self.query_data['g']

    def args_init(self, group_id):
        self.group_id = group_id

    def get_url_params(self):
        return {'g': self.group_id}

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

    async def post_actions(self, message: types.Message):
        await utils.delete_all_after_menu(message.from_user.id, message.id)
        await AppManager.get_menu().go_to_url(message.from_user.id, f'group?group={self.group_id}')


class ChangeNotifyTemplateAction(AskAction):
    @staticmethod
    def get_asker_text():
        return (
            'Введи шаблон для сообщения, отправляемого при добавлении нового ответа в бота. В шаблоне можно использовать динамические параметры:\n'
            '{lesson_name} - название урока\n'
            '{date} - дата урока',
            'чет не то')

    def query_init(self):
        self.group_id = self.query_data['g']

    def args_init(self, group_id):
        self.group_id = group_id

    def get_url_params(self):
        return {'g': self.group_id}

    def extract_data(self, message: types.Message):
        return message.text

    async def check(self, message: types.Message) -> bool:
        return bool(message.text)

    async def process_data(self, user_id, data):
        async with AppManager.get_db().cnt_mng as s:
            settings = await models.GroupSettings.get(self.group_id, session=s)
            settings.answer_notify_template = data


class DeleteGroupAction(AskAction):
    @staticmethod
    def get_asker_text():
        return ('Ты уверен? (да/нет)', '')

    def query_init(self):
        self.group_id = self.query_data['g']

    def args_init(self, group_id):
        self.group_id = group_id

    def get_url_params(self):
        return {'g': self.group_id}

    def extract_data(self, message: types.Message):
        return message.text

    async def check(self, message: types.Message) -> bool:
        return message.text == 'да'

    async def wrong_data_handler(self, message: types.Message):
        await self.post_actions(message)

    async def process_data(self, user_id, data):
        async with AppManager.get_db().cnt_mng as s:
            await s.delete(await models.GroupModel.get(self.group_id, session=s))
        await AppManager.get_menu().go_to_url(user_id, 'grouplist')


class ViewHomeworkAction(AskAction):
    def query_init(self):
        self.lesson_id = self.query_data['l']

    def args_init(self, lesson_id):
        self.lesson_id = lesson_id

    def get_url_params(self):
        return {'l': self.lesson_id}

    async def check(self, message: types.Message) -> bool:
        return message.text == '/add'

    async def do(self, query: types.CallbackQuery):
        user_id = query.from_user.id
        await self.set_asker_state(user_id)
        solutions = (await models.LessonModel.get(self.lesson_id)).solutions
        bot = AppManager.get_bot()
        if not solutions:
            await self.correct_data_handler(query)
            return

        await utils.send_solutions_with_albums(user_id, solutions)
        await bot.send_message(user_id, 'Добавить еще - /add\n\nНазад - /back')

    async def correct_data_handler(self, message: types.Message):
        query = types.CallbackQuery(0, message.from_user, None, None, None)
        await AddHomeworkAction(self.lesson_id).do(query)

    async def wrong_data_handler(self, message: types.Message):
        pass

    def extract_data(self, message: types.Message):
        pass

    async def process_data(self, user_id, data):
        pass
