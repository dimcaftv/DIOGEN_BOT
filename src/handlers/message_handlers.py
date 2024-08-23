import typing

from telebot import TeleBot, types

from app import App
from database import models
from messages import messages
from utils import states


def start_cmd_handler(message: types.Message, bot: TeleBot):
    models.UserModel(id=message.from_user.id).save()
    bot.send_message(message.chat.id, messages.start_cmd_text)


def help_cmd_handler(message: types.Message, bot: TeleBot):
    bot.send_message(message.chat.id, messages.get_help_cmd_text())


def menu_cmd_handler(message: types.Message, bot: TeleBot):
    u = models.UserModel.get(message.from_user.id)
    menu_id = u.menu_msg_id
    if menu_id:
        bot.delete_messages(message.chat.id, list(range(menu_id, message.id)))
    bot.delete_message(message.chat.id, message.id)

    ans = bot.send_message(message.chat.id, 'Загрузка...')

    u.menu_msg_id = ans.id
    App.get().menu.go_to_url(message.from_user.id, 'main')


def ask_data_handler(message: types.Message, bot: TeleBot):
    menu = App.get().menu
    asker_url = models.UserModel.get(message.from_user.id).asker_url
    menu.get_action(asker_url).wrong_data_handler(message)


def ask_data_success_handler(message: types.Message, bot: TeleBot):
    menu = App.get().menu
    asker_url = models.UserModel.get(message.from_user.id).asker_url
    menu.get_action(asker_url).correct_data_handler(message)


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
