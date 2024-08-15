import typing

from telebot import TeleBot, types

from app import App
from menu import actions
from messages import messages
from utils import states, utils


def start_cmd_handler(message: types.Message, bot: TeleBot):
    App.get().db.set_default_state(message.from_user.id)
    bot.send_message(message.chat.id, messages.start_cmd_text)


def help_cmd_handler(message: types.Message, bot: TeleBot):
    bot.send_message(message.chat.id, messages.get_help_cmd_text())


def menu_cmd_handler(message: types.Message, bot: TeleBot):
    menu_id = App.get().db.get_menu_id(message.from_user.id)
    if menu_id:
        bot.delete_messages(message.chat.id, list(range(menu_id, message.id)))
    bot.delete_message(message.chat.id, message.id)

    ans = bot.send_message(message.chat.id, 'Загрузка...')
    bot.add_data(message.from_user.id, **{utils.BotDataKeys.MENU_MSG_ID: ans.id})

    App.get().menu.go_to_url(message.from_user.id, 'main')


def ask_data_handler(message: types.Message, bot: TeleBot):
    asker: actions.AskAction = App.get().db.get_asker(message.from_user.id)
    bot.send_message(message.chat.id, asker.wrong_text)


def ask_data_success_handler(message: types.Message, bot: TeleBot):
    asker: actions.AskAction = App.get().db.get_asker(message.from_user.id)
    asker.set_answer_data(message)


cmd_handlers: typing.List[typing.Tuple[typing.Callable, typing.LiteralString]] = [
    (start_cmd_handler, 'start'),
    (help_cmd_handler, 'help'),
    (menu_cmd_handler, 'menu')
]

kwargs_handlers: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = [
    (ask_data_success_handler, {'state': states.ActionStates.ASK, 'pass_asker': True}),
    (ask_data_handler, {'state': states.ActionStates.ASK})
]


def register_handlers(bot: TeleBot):
    for cb, cmd in cmd_handlers:
        bot.register_message_handler(cb, commands=[cmd], pass_bot=True)

    for cb, kw in kwargs_handlers:
        bot.register_message_handler(cb, **kw, pass_bot=True)
