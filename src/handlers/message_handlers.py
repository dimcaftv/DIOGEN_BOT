from telebot import TeleBot, types

from app.app_manager import AppManager
from database import models
from menu.actions import TransferAction
from messages import messages
from utils import utils


def start_cmd_handler(message: types.Message, bot: TeleBot):
    models.UserModel(id=message.from_user.id, username=message.from_user.username, menu_msg_id=message.id).save()
    bot.send_message(message.chat.id, messages.start_cmd_text)


def help_cmd_handler(message: types.Message, bot: TeleBot):
    bot.send_message(message.chat.id, messages.get_help_cmd_text())


def menu_cmd_handler(message: types.Message, bot: TeleBot):
    u = models.UserModel.get(message.from_user.id)
    utils.delete_messages_range(u.id, u.menu_msg_id, message.id)

    ans = bot.send_message(message.chat.id, 'Загрузка...')

    u.menu_msg_id = ans.id
    url = 'main'
    if u.fav_group_id:
        url = TransferAction('group', {'group': u.fav_group_id}).url
    AppManager.get_menu().go_to_url(message.from_user.id, url)


def back_cmd_handler(message: types.Message, bot: TeleBot):
    user_id = message.from_user.id
    AppManager.get_menu().return_to_prev_page(user_id, message.id)


def ask_data_wrong_handler(message: types.Message, bot: TeleBot):
    menu = AppManager.get_menu()
    asker_url = models.UserModel.get(message.from_user.id).asker_url
    menu.get_action(asker_url).wrong_data_handler(message)


def ask_data_success_handler(message: types.Message, bot: TeleBot):
    menu = AppManager.get_menu()
    asker_url = models.UserModel.get(message.from_user.id).asker_url
    menu.get_action(asker_url).correct_data_handler(message)


def register_handlers(bot: TeleBot, cmd_handlers, kwargs_handlers):
    for cb, cmd in cmd_handlers:
        bot.register_message_handler(cb, commands=[cmd], pass_bot=True)

    for cb, kw in kwargs_handlers:
        bot.register_message_handler(cb, **kw, pass_bot=True)
