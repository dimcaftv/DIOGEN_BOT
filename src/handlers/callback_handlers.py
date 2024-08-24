from telebot import TeleBot, types

from app import App


def main_callback(query: types.CallbackQuery, bot: TeleBot):
    App.get().process_query(query)

    bot.answer_callback_query(query.id)


def register_handlers(bot: TeleBot, callbacks_handlers):
    for cb, kw in callbacks_handlers:
        bot.register_callback_query_handler(cb, None, True, **kw)
