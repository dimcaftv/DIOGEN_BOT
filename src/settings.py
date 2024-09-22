import os
import typing

import dotenv
from telebot import asyncio_filters
from telebot.util import content_type_media

from handlers import callback_handlers, message_handlers
from menu import actions, pages
from utils import commands, states

dotenv.load_dotenv('../.env')

DEBUG = os.getenv('DEBUG') == '1'

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_FULL_PATH = os.getenv('DB_PATH')
TMP_USER_DATA_PATH = os.getenv('TMP_USER_DATA_PATH')

MEDIA_STORAGE_TG_ID = os.getenv('MEDIA_STORAGE_ID')

kwargs_handlers: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = [
    (message_handlers.asker_handler, {'content_types': content_type_media, 'state': states.ActionStates.ASK})
]

callbacks_handlers: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = [
    (callback_handlers.main_callback, {'state': '*'})
]

commands_list = [
    commands.FullCommand('start', message_handlers.start_cmd_handler, 'запуск бота'),
    commands.FullCommand('help', message_handlers.help_cmd_handler, 'показать помощь'),
    commands.FullCommand('menu', message_handlers.menu_cmd_handler, 'открыть главное меню'),
    commands.FullCommand('back', message_handlers.back_cmd_handler,
                         'отменить текущее действие или удалить лишние сообщения'),
]

bot_filters = [
    asyncio_filters.StateFilter
]

pages_list = [
    pages.MainPage,
    pages.GroupListPage,
    pages.GroupPage,
    pages.TimetablePage,
    pages.DayPage,
    pages.LessonPage,
    pages.UsersListPage,
    pages.ActiveInvitesPage
]

actions_list = [
    actions.TransferAction,
    actions.CreateGroupAction,
    actions.DeleteGroupAction,
    actions.CreateInviteAction,
    actions.JoinGroupAction,
    actions.KickUserAction,
    actions.CreateTimetableAction,
    actions.CopyPrevTimetableAction,
    actions.ViewHomeworkAction,
    actions.AddHomeworkAction,
    actions.ViewRecentHomeworkAction
]
