import asyncio

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.util import extract_arguments

from app.app_manager import AppManager
from database import models
from menu.actions.actions import TransferAction
from messages import messages
from utils import utils
from utils.commands import FullCommand


async def start_cmd_handler(message: types.Message, bot: AsyncTeleBot):
    async with AppManager.get_db().cnt_mng as s:
        await s.merge(models.UserModel(id=message.from_user.id, username=message.from_user.username))

    await AppManager.get_db().dynamic_user_data.storage.set_default_state(message.from_user.id)
    asyncio.create_task(bot.send_message(message.chat.id, messages.start_cmd_text))


async def help_cmd_handler(message: types.Message, bot: AsyncTeleBot):
    asyncio.create_task(bot.send_message(message.chat.id, messages.get_help_cmd_text()))


async def menu_cmd_handler(message: types.Message, bot: AsyncTeleBot):
    user_id = message.from_user.id
    u = await models.UserModel.get(user_id)

    mmid = (await models.UserDataclass.get_user(user_id)).menu_msg_id
    if mmid == 0:
        mmid = message.id
    await utils.delete_messages_range(user_id, mmid, message.id)

    ans = await bot.send_message(message.chat.id, 'Загрузка...')

    mmid = ans.id
    (await models.UserDataclass.get_user(user_id)).menu_msg_id = mmid

    url = 'main'
    if u.fav_group_id:
        url = TransferAction('group', {'group': u.fav_group_id}).url

    await AppManager.get_menu().go_to_url(user_id, url)


async def back_cmd_handler(message: types.Message, bot: AsyncTeleBot):
    user_id = message.from_user.id
    await AppManager.get_menu().return_to_prev_page(user_id, message.id)


async def addchat_cmd_handler(message: types.Message, bot: AsyncTeleBot):
    link = extract_arguments(message.text)
    if not link:
        await bot.send_message(message.chat.id, 'Напиши код приглашения в группу после команды через пробел')
        return

    async with AppManager.get_db().cnt_mng as s:
        invite = await models.GroupInviteModel.get(link, session=s)
        if invite is None:
            await bot.send_message(message.chat.id, 'такого приглашения нет')
            return
        invite.group.settings.general_group_chat_id = message.chat.id
        gname = invite.group.name
    await bot.send_message(message.chat.id, f'Этот чат теперь прикреплен к "{gname}"')


async def asker_handler(message: types.Message, bot: AsyncTeleBot):
    menu = AppManager.get_menu()
    asker_url = (await models.UserDataclass.get_user(message.from_user.id)).asker_url
    await menu.get_action(asker_url).message_handler(message)


def register_handlers(bot: AsyncTeleBot, cmd_handlers: list[FullCommand], kwargs_handlers):
    for cmd in cmd_handlers:
        bot.register_message_handler(cmd.handler, commands=[cmd.name], **cmd.kwargs, pass_bot=True)

    for cb, kw in kwargs_handlers:
        bot.register_message_handler(cb, **kw, pass_bot=True)
