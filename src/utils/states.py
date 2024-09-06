from telebot import State
from telebot.handler_backends import StatesGroup


class AbsAdvancedState(State):
    pass


class BotPagesStates(StatesGroup):
    MAIN = State()
    GROUPLIST = State()
    GROUP = State()
    TIMETABLE = State()
    DAY = State()
    LESSON = State()
    USERSLIST = State()
    ACTIVE_INVITES = State()


class ActionStates(StatesGroup):
    ASK = State()
