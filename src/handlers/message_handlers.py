import typing

from telebot import TeleBot, types

from utils import utils


def menu_cmd_handler(message: types.Message, bot: TeleBot):
    bot.set_state(message.from_user.id, utils.BotPagesStates.MAIN)
    bot.send_message(message.chat.id,
                     **utils.get_message_for_page(
                             utils.main_menu.get_page_from_state(
                                     utils.BotPagesStates.MAIN)))


cmd_handlers: typing.List[typing.Tuple[typing.Callable, typing.LiteralString]] = [
    (menu_cmd_handler, 'menu')
]

kwargs_handlers: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = []


def register_handlers(bot: TeleBot):
    for cb, cmd in cmd_handlers:
        bot.register_message_handler(cb, commands=[cmd], pass_bot=True)

    for cb, kw in kwargs_handlers:
        bot.register_message_handler(cb, **kw, pass_bot=True)
