from urllib.parse import urlencode

from app import App
from menu.actions import AskAction, TransferAction
from menu.menu import AbsMenuPage, MenuItem
from utils import states


class MainPage(AbsMenuPage):
    state = states.BotPagesStates.MAIN

    def get_items(self) -> list[MenuItem]:
        return [
            MenuItem('группы', 'groups', TransferAction(states.BotPagesStates.GROUPLIST))
        ]

    def get_page_text(self) -> str:
        return f'Hey {self.user_id}, this is MAIN PAGE'


class GroupListPage(AbsMenuPage):
    state = states.BotPagesStates.GROUPLIST

    def get_items(self) -> list[MenuItem]:
        if self.data.get('ask_data'):
            App.get().db.create_group(self.user_id, self.data['ask_data'])

        groupItems = [
            MenuItem(g.name, 'group?' + urlencode({'group': g.id}), TransferAction(states.BotPagesStates.GROUP)) for g
            in
            App.get().db.get_user_groups(self.user_id)]

        return groupItems + [
            MenuItem('добавить', 'add', AskAction(
                    lambda x: bool(x.text),
                    self.state,
                    'Введи название новой группы',
                    'Бро, это не название'
            )),
            MenuItem('назад', 'back', TransferAction(states.BotPagesStates.MAIN))
        ]

    def get_page_text(self) -> str:
        return f'Hey {self.user_id}, this is GROUPLIST PAGE'


class GroupPage(AbsMenuPage):
    state = states.BotPagesStates.GROUP

    def get_items(self) -> list[MenuItem]:
        return [
            MenuItem('дз', 'hw?' + urlencode({'group': self.data["group"]}),
                     TransferAction(states.BotPagesStates.HOMEWORK)),
            MenuItem('назад', 'back', TransferAction(states.BotPagesStates.GROUPLIST))
        ]

    def get_page_text(self) -> str:
        return f'Hey {self.user_id}, this is {self.data["group"]} group PAGE'


class HomeworkPage(AbsMenuPage):
    state = states.BotPagesStates.HOMEWORK

    def get_items(self) -> list[MenuItem]:
        return [MenuItem('назад', 'back?' + urlencode({'group': self.data["group"]}),
                         TransferAction(states.BotPagesStates.GROUP))]

    def get_page_text(self) -> str:
        return f'Hey {self.user_id}, this is {self.data["group"]} homework PAGE'
