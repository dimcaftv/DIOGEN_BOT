import os
import typing

import dotenv
from telebot import asyncio_filters
from telebot.util import content_type_media

from handlers import callback_handlers, message_handlers
from menu import pages
from menu.actions import actions, ask_actions
from utils import commands, filters, states

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
    commands.FullCommand('start', message_handlers.start_cmd_handler, 'запуск бота', isdm=True),
    commands.FullCommand('help', message_handlers.help_cmd_handler, 'показать помощь', isdm=True),
    commands.FullCommand('menu', message_handlers.menu_cmd_handler, 'открыть главное меню', isdm=True),
    commands.FullCommand('back', message_handlers.back_cmd_handler,
                         'отменить текущее действие или удалить лишние сообщения', isdm=True),
    commands.FullCommand('addchat', message_handlers.addchat_cmd_handler,
                         'добавить эту группу для отправки уведомлений (напиши код приглашения в группу через пробел)',
                         isdm=False, is_chat_admin=True),
]

bot_filters = [
    asyncio_filters.StateFilter,
    filters.InDmFilter,
    asyncio_filters.IsAdminFilter
]

pages_list = [
    pages.MainPage,
    pages.GroupListPage,
    pages.GroupPage,
    pages.TimetablePage,
    pages.DayPage,
    pages.LessonPage,
    pages.UsersListPage,
    pages.ActiveInvitesPage,
    pages.GroupSettingsPage
]

actions_list = [
    actions.TransferAction,
    actions.DeleteGroupAction,
    actions.CopyPrevTimetableAction,
    actions.ViewHomeworkAction,
    actions.ViewRecentHomeworkAction,
    actions.FlipNotifyAction,
    ask_actions.CreateGroupAction,
    ask_actions.CreateInviteAction,
    ask_actions.JoinGroupAction,
    ask_actions.KickUserAction,
    ask_actions.CreateTimetableAction,
    ask_actions.AddHomeworkAction,
    ask_actions.ChangeGroupAdminAction,
    ask_actions.ChangeNotifyTemplateAction
]
