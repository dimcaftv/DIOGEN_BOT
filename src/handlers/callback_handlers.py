import typing

from telebot import TeleBot

callbacks: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = []


def register_handlers(bot: TeleBot):
    for cb, kw in callbacks:
        bot.register_callback_query_handler(cb, None, True, **kw)
