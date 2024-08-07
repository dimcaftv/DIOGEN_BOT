import typing

from telebot import TeleBot

cmd_handlers: typing.List[typing.Tuple[typing.Callable, typing.LiteralString]] = []

kwargs_handlers: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = []


def register_handlers(bot: TeleBot):
    for cb, cmd in cmd_handlers:
        bot.register_message_handler(cb, commands=[cmd], pass_bot=True)

    for cb, kw in kwargs_handlers:
        bot.register_message_handler(cb, **kw, pass_bot=True)
