import typing

from telebot import TeleBot, types

import menu.utils
from database.database import SimpleBotStateStorage
from messages import messages
from utils import utils, states


def start_cmd_handler(message: types.Message, bot: TeleBot):
    SimpleBotStateStorage().set_default_state(message.from_user.id)
    bot.send_message(message.chat.id, messages.start_cmd_text)


def help_cmd_handler(message: types.Message, bot: TeleBot):
    bot.send_message(message.chat.id, messages.get_help_cmd_text())


def menu_cmd_handler(message: types.Message, bot: TeleBot):
    bot.set_state(message.from_user.id, states.BotPagesStates.MAIN)
    menu_id = SimpleBotStateStorage().get_data(message.from_user.id).get(utils.BotDataKeys.MENU_MSG_ID.value)
    if menu_id:
        bot.delete_message(message.chat.id, menu_id)
    ans = bot.send_message(message.chat.id,
                           **menu.utils.main_menu.get_page_from_state(states.BotPagesStates.MAIN).get_message_kw(
                                   message.from_user.id))
    bot.add_data(message.from_user.id, **{utils.BotDataKeys.MENU_MSG_ID.value: ans.id})
    bot.delete_message(message.chat.id, message.id)


cmd_handlers: typing.List[typing.Tuple[typing.Callable, typing.LiteralString]] = [
    (start_cmd_handler, 'start'),
    (help_cmd_handler, 'help'),
    (menu_cmd_handler, 'menu')
]

kwargs_handlers: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = []


def register_handlers(bot: TeleBot):
    for cb, cmd in cmd_handlers:
        bot.register_message_handler(cb, commands=[cmd], pass_bot=True)

    for cb, kw in kwargs_handlers:
        bot.register_message_handler(cb, **kw, pass_bot=True)
