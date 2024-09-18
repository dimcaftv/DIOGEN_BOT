import os
import typing

import dotenv
from telebot import asyncio_filters, types
from telebot.util import content_type_media

from handlers import callback_handlers, message_handlers
from menu import actions, pages
from utils import states

dotenv.load_dotenv('../.env')

DEBUG = os.getenv('DEBUG') == '1'

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_FULL_PATH = os.getenv('DB_PATH')
TMP_USER_DATA_PATH = os.getenv('TMP_USER_DATA_PATH')

MEDIA_STORAGE_TG_ID = os.getenv('MEDIA_STORAGE_ID')

cmd_handlers: typing.List[typing.Tuple[typing.Callable, typing.LiteralString]] = [
    (message_handlers.start_cmd_handler, 'start'),
    (message_handlers.help_cmd_handler, 'help'),
    (message_handlers.menu_cmd_handler, 'menu'),
    (message_handlers.back_cmd_handler, 'back')
]

kwargs_handlers: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = [
    (message_handlers.asker_handler, {'content_types': content_type_media, 'state': states.ActionStates.ASK})
]

callbacks_handlers: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = [
    (callback_handlers.main_callback, {'state': '*'})
]

commands_list = [
    types.BotCommand('start', 'запуск бота'),
    types.BotCommand('help', 'показать помощь'),
    types.BotCommand('menu', 'открыть главное меню'),
    types.BotCommand('back', 'отменить текущее действие или удалить лишние сообщения')
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
