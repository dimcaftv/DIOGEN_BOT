from datetime import date, timedelta

from sqlalchemy import or_
from telebot import types

from app.app_manager import AppManager
from database import models
from utils import utils
from utils.calendar import Week
from . import Action
from ..urls import encode_url


class TransferAction(Action):
    def query_init(self):
        self.url = self.query_data['url']

    def args_init(self, base_url: str = 'main', data: dict = None):
        data = data or {}
        self.url = encode_url(base_url, data)

    def get_url_params(self):
        return {'url': self.url}

    async def do(self, query: types.CallbackQuery):
        try:
            await AppManager.get_menu().go_to_url(query.from_user.id, self.url)
        except Exception as e:
            print(e)
            await AppManager.get_menu().go_to_url(query.from_user.id, 'main')


class CopyPrevTimetableAction(Action):
    def query_init(self):
        self.group_id = self.query_data['g']
        self.week = Week.from_str(self.query_data['w'])

    def args_init(self, group_id, week):
        self.group_id = group_id
        self.week = week

    def get_url_params(self):
        return {'g': self.group_id, 'w': self.week}

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


class ViewRecentHomeworkAction(Action):
    def query_init(self):
        self.group_id = self.query_data['g']

    def args_init(self, group_id):
        self.group_id = group_id

    def get_url_params(self):
        return {'g': self.group_id}

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
            await bot.send_message(user_id, f'📕 {l.name} {Week.standart_day_format(l.date)}')
            await utils.send_solutions_with_albums(user_id, sols)
        await bot.send_message(user_id, 'Назад - /back')


class FlipNotifyAction(Action):
    def query_init(self):
        self.group_id = self.query_data['g']

    def args_init(self, group_id):
        self.group_id = group_id

    def get_url_params(self):
        return {'g': self.group_id}

    async def do(self, query: types.CallbackQuery):
        async with AppManager.get_db().cnt_mng as s:
            settings = await models.GroupSettings.get(self.group_id, session=s)
            settings.new_answer_notify = not settings.new_answer_notify
        await AppManager.get_menu().go_to_last_url(query.from_user.id)
