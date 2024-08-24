from telebot import TeleBot, custom_filters, types

from app import App
from database import models
from utils import utils


def is_group_admin(user_id: int, group_id: int):
    return models.GroupModel.get(group_id).admin_id == user_id


class AskerFilter(custom_filters.SimpleCustomFilter):
    key = 'pass_asker'

    def check(self, message: types.Message):
        menu = App.get().menu

        asker_url = models.UserModel.get(message.from_user.id).asker_url
        return menu.get_action(asker_url).check(message)


def register_filters(bot: TeleBot, filters):
    for f in filters:
        args = []
        if utils.is_init_takes_one_arg(f):
            args.append(bot)
        bot.add_custom_filter(f(*args))
