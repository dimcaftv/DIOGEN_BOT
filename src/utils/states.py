from telebot import State
from telebot.handler_backends import StatesGroup


class AbsAdvancedState(State):
    def get_message_text(self, user_id):
        raise NotImplementedError


class MainState(AbsAdvancedState):
    def get_message_text(self, user_id):
        return f'bro, {user_id}, это MAIN state'


class GroupListState(AbsAdvancedState):
    def get_message_text(self, user_id):
        return f'bro, {user_id}, это GROUPLIST state'


class GroupState(AbsAdvancedState):
    def get_message_text(self, user_id):
        return f'bro, {user_id}, это GROUP state'


class HomeworkState(AbsAdvancedState):
    def get_message_text(self, user_id):
        return f'bro, {user_id}, это HOMEWORK state'


class BotPagesStates(StatesGroup):
    MAIN = MainState()
    GROUPLIST = GroupListState()
    GROUP = GroupState()
    HOMEWORK = HomeworkState()
