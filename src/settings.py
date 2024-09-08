import os
import typing

from telebot import custom_filters, types

from handlers import callback_handlers, message_handlers
from menu import actions, pages
from utils import filters, states

DEBUG = True

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_FULL_PATH = os.getenv('DB_PATH')

MEDIA_STORAGE_TG_ID = os.getenv('MEDIA_STORAGE_ID')

cmd_handlers: typing.List[typing.Tuple[typing.Callable, typing.LiteralString]] = [
    (message_handlers.start_cmd_handler, 'start'),
    (message_handlers.help_cmd_handler, 'help'),
    (message_handlers.menu_cmd_handler, 'menu'),
    (message_handlers.back_cmd_handler, 'back')
]

kwargs_handlers: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = [
    (message_handlers.ask_data_success_handler, {'state': states.ActionStates.ASK, 'pass_asker': True}),
    (message_handlers.ask_data_wrong_handler, {'state': states.ActionStates.ASK})
]

callbacks_handlers: typing.List[typing.Tuple[typing.Callable, typing.Mapping]] = [
    (callback_handlers.main_callback, {'state': '*'})
]

commands_list = [
    types.BotCommand('start', 'запуск бота'),
    types.BotCommand('help', 'показать помощь'),
    types.BotCommand('menu', 'открыть главное меню'),
    types.BotCommand('back', 'отменить текущее действие')
]

bot_filters = [custom_filters.StateFilter,
               custom_filters.IsDigitFilter,
               custom_filters.TextMatchFilter,
               filters.AskerFilter]

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
    actions.AddHomeworkAction
]
