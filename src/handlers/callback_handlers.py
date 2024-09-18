from telebot import types
from telebot.async_telebot import AsyncTeleBot

from app.app_manager import AppManager
from database import models


async def main_callback(query: types.CallbackQuery, bot: AsyncTeleBot):
    data, user_id = query.data, query.from_user.id

    await models.UserDataclass.set_by_key(user_id, 'menu_msg_id', query.message.id)
    if data == '-':
        await bot.answer_callback_query(query.id)
        return

    action = AppManager.get_menu().get_action(data)
    await action.do(query)
    await bot.answer_callback_query(query.id)


def register_handlers(bot: AsyncTeleBot, callbacks_handlers):
    for cb, kw in callbacks_handlers:
        bot.register_callback_query_handler(cb, None, True, **kw)
