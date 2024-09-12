from telebot import TeleBot, types

from app.app_manager import AppManager
from database import models


def main_callback(query: types.CallbackQuery, bot: TeleBot):
    data, user_id = query.data, query.from_user.id
    models.UserModel.get(query.from_user.id).menu_msg_id = query.message.id
    action = AppManager.get_menu().get_action(data)
    action.do(query)
    bot.answer_callback_query(query.id)


def register_handlers(bot: TeleBot, callbacks_handlers):
    for cb, kw in callbacks_handlers:
        bot.register_callback_query_handler(cb, None, True, **kw)
