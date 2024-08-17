import abc

from telebot import TeleBot, custom_filters, types

from app import App
from utils import utils


class MenuItemFilter(abc.ABC):
    @abc.abstractmethod
    def check(self, user_id):
        raise NotImplementedError


class AskerFilter(custom_filters.SimpleCustomFilter):
    key = 'pass_asker'

    def check(self, message: types.Message):
        menu = App.get().menu
        asker_url = App.get().db.get_data(message.from_user.id)[utils.BotDataKeys.ASKER_URL]
        return menu.get_action(asker_url).check(message)


def register_filters(bot: TeleBot):
    bot_filters = [custom_filters.StateFilter(bot),
                   custom_filters.IsDigitFilter(),
                   custom_filters.TextMatchFilter(),
                   AskerFilter()]

    for f in bot_filters:
        bot.add_custom_filter(f)
