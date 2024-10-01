from telebot.asyncio_handler_backends import State, StatesGroup


class UserStates(StatesGroup):
    MENU = State()
    ASK = State()
