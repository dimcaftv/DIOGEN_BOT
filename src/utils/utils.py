import asyncio
import math
from types import FunctionType
from uuid import uuid4

from app.app_manager import AppManager
from database import models


async def get_tg_user(user_id: int):
    return (await AppManager.get_bot().get_chat_member(user_id, user_id)).user


def generate_invite_link():
    links = [i.link for i in models.GroupInviteModel.select().all()]
    while (l := uuid4().hex[:6]) in links:
        continue
    return l


def is_init_takes_one_arg(cls):
    return isinstance(cls.__init__, FunctionType) and cls.__init__.__code__.co_argcount == 2


async def delete_messages_range(user_id, from_id, to_id):
    bot = AppManager.get_bot()
    l = to_id - from_id + 1
    for i in range(math.ceil(l / 100)):
        try:
            asyncio.create_task(
                bot.delete_messages(user_id, list(range(from_id + i * 100, min(from_id + (i + 1) * 100, to_id + 1)))))
        except:
            pass


async def delete_all_after_menu(user_id, last_id):
    menu_id = await models.UserDataclass.get_by_key(user_id, 'menu_msg_id')
    await delete_messages_range(user_id, menu_id + 1, last_id)
