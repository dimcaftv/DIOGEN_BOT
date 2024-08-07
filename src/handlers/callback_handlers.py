import typing

from telebot import TeleBot, types

from utils import utils


def main_callback(query: types.CallbackQuery, bot: TeleBot):
    to_state = utils.main_menu.get_transfer_state(bot.get_state(query.from_user.id), query.data)
    bot.set_state(query.from_user.id, to_state)
    bot.edit_message_text(chat_id=query.message.chat.id,
                          message_id=query.message.id,
                          **utils.get_message_for_page(
                                  utils.main_menu.get_page_from_state(to_state)))


callbacks: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = [
    (main_callback, {'state': '*'})
]


def register_handlers(bot: TeleBot):
    for cb, kw in callbacks:
        bot.register_callback_query_handler(cb, None, True, **kw)
