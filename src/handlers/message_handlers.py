from telebot import TeleBot, types

from app.app_manager import AppManager
from database import models
from menu.actions import TransferAction
from messages import messages
from utils import utils


def start_cmd_handler(message: types.Message, bot: TeleBot):
    with AppManager.get_db().cnt_mng as s:
        s.merge(models.UserModel(id=message.from_user.id, username=message.from_user.username))

    AppManager.get_db().dynamic_user_data.storage.set_default_state(message.from_user.id)
    bot.send_message(message.chat.id, messages.start_cmd_text)


def help_cmd_handler(message: types.Message, bot: TeleBot):
    bot.send_message(message.chat.id, messages.get_help_cmd_text())


def menu_cmd_handler(message: types.Message, bot: TeleBot):
    user_id = message.from_user.id
    u = models.UserModel.get(user_id)
    mmid = models.UserDataclass.get_by_key(user_id, 'menu_msg_id')

    utils.delete_messages_range(user_id, mmid, message.id)

    ans = bot.send_message(message.chat.id, 'Загрузка...')

    mmid = ans.id
    models.UserDataclass.set_by_key(user_id, 'menu_msg_id', mmid)

    url = 'main'
    if u.fav_group_id:
        url = TransferAction('group', {'group': u.fav_group_id}).url

    AppManager.get_menu().go_to_url(user_id, url)


def back_cmd_handler(message: types.Message, bot: TeleBot):
    user_id = message.from_user.id
    AppManager.get_menu().return_to_prev_page(user_id, message.id)


def asker_handler(message: types.Message, bot: TeleBot):
    menu = AppManager.get_menu()
    asker_url = AppManager.get_db().dynamic_user_data.get_by_key(message.from_user.id, 'asker_url')
    menu.get_action(asker_url).message_handler(message)


def register_handlers(bot: TeleBot, cmd_handlers, kwargs_handlers):
    for cb, cmd in cmd_handlers:
        bot.register_message_handler(cb, commands=[cmd], pass_bot=True)

    for cb, kw in kwargs_handlers:
        bot.register_message_handler(cb, **kw, pass_bot=True)
