from app import App
from menu.actions import AskAction, TransferAction
from menu.menu import AbsMenuPage, MenuItem
from utils import states


class MainPage(AbsMenuPage):
    state = states.BotPagesStates.MAIN
    urlpath = 'main'

    def get_items(self) -> list[MenuItem]:
        return [
            MenuItem('группы', TransferAction('grouplist'))
        ]

    def get_page_text(self) -> str:
        return f'Hey {self.user_id}, this is MAIN PAGE'


class GroupListPage(AbsMenuPage):
    state = states.BotPagesStates.GROUPLIST
    urlpath = 'grouplist'

    def get_items(self) -> list[MenuItem]:
        if self.data.get('ask_data'):
            App.get().db.create_group(self.user_id, self.data['ask_data'])

        groupItems = [
            MenuItem(g.name, TransferAction('group', {'group': g.id}))
            for g in App.get().db.get_user_groups(self.user_id)
        ]

        return groupItems + [
            MenuItem('добавить', AskAction(
                    lambda x: bool(x.text),
                    'Введи название новой группы',
                    'Бро, это не название'
            )),
            MenuItem('назад', TransferAction('main'))
        ]

    def get_page_text(self) -> str:
        return f'Hey {self.user_id}, this is GROUPLIST PAGE'


class GroupPage(AbsMenuPage):
    state = states.BotPagesStates.GROUP
    urlpath = 'group'

    def get_items(self) -> list[MenuItem]:
        return [
            MenuItem('дз', TransferAction('homework', {'group': self.query_data['group']})),
            MenuItem('назад', TransferAction('grouplist'))
        ]

    def get_page_text(self) -> str:
        return f'Hey {self.user_id}, this is {self.query_data["group"]} group PAGE'


class HomeworkPage(AbsMenuPage):
    state = states.BotPagesStates.HOMEWORK
    urlpath = 'homework'

    def get_items(self) -> list[MenuItem]:
        return [MenuItem('назад', TransferAction('group', {'group': self.query_data['group']}))]

    def get_page_text(self) -> str:
        return f'Hey {self.user_id}, this is {self.query_data["group"]} homework PAGE'
