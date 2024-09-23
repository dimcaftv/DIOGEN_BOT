from telebot import asyncio_filters, types
from telebot.async_telebot import AsyncTeleBot

from utils import utils


class InDmFilter(asyncio_filters.SimpleCustomFilter):
    key = 'isdm'

    async def check(self, message: types.Message) -> bool:
        return utils.is_msg_from_dm(message)


def register_filters(bot: AsyncTeleBot, filters):
    for f in filters:
        args = []
        if utils.is_init_takes_one_arg(f):
            args.append(bot)
        bot.add_custom_filter(f(*args))
