from telebot.asyncio_handler_backends import State, StatesGroup


class BotPagesStates(StatesGroup):
    MAIN = State()
    GROUPLIST = State()
    GROUP = State()
    TIMETABLE = State()
    DAY = State()
    LESSON = State()
    USERSLIST = State()
    ACTIVE_INVITES = State()
    GROUP_SETTINGS = State()


class ActionStates(StatesGroup):
    ASK = State()
