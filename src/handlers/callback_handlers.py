import typing

from telebot import TeleBot, types

from app import App


def main_callback(query: types.CallbackQuery, bot: TeleBot):
    App.get().process_query(query)

    bot.answer_callback_query(query.id)


callbacks: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = [
    (main_callback, {'state': '*'})
]


def register_handlers(bot: TeleBot):
    for cb, kw in callbacks:
        bot.register_callback_query_handler(cb, None, True, **kw)
