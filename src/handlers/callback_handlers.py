import typing

from telebot import TeleBot, types

from menu import utils


def main_callback(query: types.CallbackQuery, bot: TeleBot):
    to_state = utils.main_menu.get_transfer_state(bot.get_state(query.from_user.id), query.data)
    bot.set_state(query.from_user.id, to_state)
    bot.edit_message_text(chat_id=query.message.chat.id,
                          message_id=query.message.id,
                          **utils.main_menu.get_page_from_state(to_state).get_message_kw(query.from_user.id))


callbacks: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = [
    (main_callback, {'state': '*'})
]


def register_handlers(bot: TeleBot):
    for cb, kw in callbacks:
        bot.register_callback_query_handler(cb, None, True, **kw)
