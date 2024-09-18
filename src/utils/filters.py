from telebot.async_telebot import AsyncTeleBot

from utils import utils


def register_filters(bot: AsyncTeleBot, filters):
    for f in filters:
        args = []
        if utils.is_init_takes_one_arg(f):
            args.append(bot)
        bot.add_custom_filter(f(*args))
