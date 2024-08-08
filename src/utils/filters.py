import abc

from telebot import TeleBot, custom_filters


class MenuItemFilter(abc.ABC):
    @abc.abstractmethod
    def check(self, user_id):
        raise NotImplementedError


def register_filters(bot: TeleBot):
    bot_filters = [custom_filters.StateFilter(bot),
                   custom_filters.IsDigitFilter(),
                   custom_filters.TextMatchFilter()]

    for f in bot_filters:
        bot.add_custom_filter(f)
