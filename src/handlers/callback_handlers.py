from telebot import TeleBot, types

from app.app_manager import AppManager


def main_callback(query: types.CallbackQuery, bot: TeleBot):
    data, user_id = query.data, query.from_user.id
    action = AppManager.get_menu().get_action(data)
    action.do(query)
    bot.answer_callback_query(query.id)


def register_handlers(bot: TeleBot, callbacks_handlers):
    for cb, kw in callbacks_handlers:
        bot.register_callback_query_handler(cb, None, True, **kw)
