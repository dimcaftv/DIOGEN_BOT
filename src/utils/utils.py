import asyncio
import math
from itertools import groupby
from types import FunctionType
from uuid import uuid4

from telebot import types
from telebot.types import InputMediaPhoto

import settings
from app.app_manager import AppManager
from database import models


async def get_tg_user(user_id: int):
    return (await AppManager.get_bot().get_chat_member(user_id, user_id)).user


async def generate_invite_link():
    links = [i.link for i in (await models.GroupInviteModel.select()).all()]
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
                    bot.delete_messages(user_id,
                                        list(range(from_id + i * 100, min(from_id + (i + 1) * 100, to_id + 1)))))
        except:
            pass


async def delete_all_after_menu(user_id, last_id):
    menu_id = await models.UserDataclass.get_by_key(user_id, 'menu_msg_id')
    await delete_messages_range(user_id, menu_id + 1, last_id)


def sep_list(l: list, n: int):
    res = []
    for i in range(0, len(l), n):
        res.append(l[i:i + n])
    return res


def is_msg_from_dm(message: types.Message):
    return message.chat.type == 'private'


async def send_solutions_with_albums(user_id: int, solutions: list['models.SolutionModel']):
    solutions.sort(key=lambda x: x.author_id)
    i = 0
    for _, author_sols in groupby(solutions, key=lambda x: x.author_id):
        author_sols = list(author_sols)
        i += 1
        media_sols = [s for s in author_sols if s.file_id]
        normis_sols = [s for s in author_sols if s.file_id is None]

        media_groups = sep_list(media_sols, 10)
        if media_groups and len(media_groups[-1]) == 1:
            normis_sols = media_groups.pop(-1) + normis_sols

        bot = AppManager.get_bot()
        await bot.send_message(user_id, f'📘 Решение #{i}')
        for g in media_groups:
            await bot.send_media_group(user_id, [InputMediaPhoto(s.file_id) for s in g])
        if normis_sols:
            await bot.copy_messages(user_id, settings.MEDIA_STORAGE_TG_ID, sorted([s.msg_id for s in normis_sols]))
