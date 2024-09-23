from datetime import date, timedelta
from urllib.parse import urlencode

from sqlalchemy import or_
from telebot import types

from app.app_manager import AppManager
from database import models
from utils import utils
from utils.calendar import Week
from . import Action


class TransferAction(Action):
    key = 'transfer'
    take_params = True

    def __init__(self, base_url: str = 'main', data: dict = None, full_data: str = None):
        data = data or {}
        if full_data:
            self.url = full_data
        else:
            self.url = base_url + '?' + urlencode(data)

    def get_url_params(self):
        return self.url

    async def do(self, query: types.CallbackQuery):
        try:
            await AppManager.get_menu().go_to_url(query.from_user.id, self.url)
        except Exception as e:
            print(e)
            await AppManager.get_menu().go_to_url(query.from_user.id, 'main')


class DeleteGroupAction(Action):
    key = 'delete_group'
    take_params = True

    def __init__(self, full_data):
        self.group_id = int(full_data)

    async def do(self, query: types.CallbackQuery):
        async with AppManager.get_db().cnt_mng as s:
            await s.delete(await models.GroupModel.get(self.group_id, session=s))
        await AppManager.get_menu().go_to_url(query.from_user.id, 'grouplist')

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

    async def do(self, query: types.CallbackQuery):
        pweek = self.week.prev()
        lessons = []
        async with AppManager.get_db().cnt_mng as s:
            for d1, d2 in zip(pweek, self.week):
                await models.LessonModel.delete_where(models.LessonModel.date == d2,
                                                      models.LessonModel.group_id == self.group_id, session=s)
                for l in (await models.LessonModel.select(models.LessonModel.date == d1,
                                                          models.LessonModel.group_id == self.group_id)).all():
                    lessons.append(models.LessonModel(date=d2, group_id=self.group_id, name=l.name))
            s.add_all(lessons)


class ViewHomeworkAction(Action):
    key = 'view_homework'
    take_params = True

    def __init__(self, full_data=None):
        self.lesson_id = int(full_data)

    def get_url_params(self):
        return str(self.lesson_id)

    async def do(self, query: types.CallbackQuery):
        user_id = query.from_user.id
        solutions = (await models.LessonModel.get(self.lesson_id)).solutions
        bot = AppManager.get_bot()
        if not solutions:
            await bot.answer_callback_query(query.id, 'На этот урок ничего нет', True)
            return

        await utils.send_solutions_with_albums(user_id, solutions)
        await bot.send_message(user_id, 'Назад - /back')


class ViewRecentHomeworkAction(Action):
    key = 'view_recent_homework'
    take_params = True

    def __init__(self, full_data=None):
        self.group_id = int(full_data)

    def get_url_params(self):
        return str(self.group_id)

    async def do(self, query: types.CallbackQuery):
        bot = AppManager.get_bot()
        user_id = query.from_user.id
        lessons = (await models.LessonModel.select(or_(models.LessonModel.date == date.today(),
                                                       models.LessonModel.date == date.today() + timedelta(days=1)),
                                                   models.LessonModel.group_id == self.group_id)).all()
        for l in lessons:
            sols = l.solutions
            if not sols:
                continue
            await bot.send_message(user_id, f'📘 {l.name} {Week.standart_day_format(l.date)}')
            await utils.send_solutions_with_albums(user_id, sols)
        await bot.send_message(user_id, 'Назад - /back')


class FlipNotifyAction(Action):
    key = 'flip_notify'
    take_params = True

    def __init__(self, full_data=None):
        self.group_id = int(full_data)

    def get_url_params(self):
        return str(self.group_id)

    async def do(self, query: types.CallbackQuery):
        async with AppManager.get_db().cnt_mng as s:
            settings = await models.GroupSettings.get(self.group_id, session=s)
            settings.new_answer_notify = not settings.new_answer_notify
        await AppManager.get_menu().go_to_last_url(query.from_user.id)
