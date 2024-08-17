from app import App
from menu.actions import AddGroupAction, DeleteGroupAction, TransferAction
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
        return f'Hey {self.user.username}, this is MAIN PAGE'


class GroupListPage(AbsMenuPage):
    state = states.BotPagesStates.GROUPLIST
    urlpath = 'grouplist'

    def get_items(self) -> list[MenuItem]:
        self.groups = App.get().db.get_user_groups(self.user.id)

        groupItems = [
            MenuItem(g.name, TransferAction('group', {'group': g.id}))
            for g in self.groups
        ]

        return groupItems + [
            MenuItem('добавить', AddGroupAction()),
            MenuItem('удалить', DeleteGroupAction()),
            MenuItem('назад', TransferAction('main'))
        ]

    def get_page_text(self) -> str:
        return f'Hey {self.user.username}, this is GROUPLIST PAGE\n' + '\n'.join(
                f'{g.id}: {g.name}' for g in self.groups)


class GroupPage(AbsMenuPage):
    state = states.BotPagesStates.GROUP
    urlpath = 'group'

    def get_items(self) -> list[MenuItem]:
        self.group = App.get().db.get_group(self.query_data['group'])

        return [
            MenuItem('дз', TransferAction('homework', {'group': self.group.id})),
            MenuItem('назад', TransferAction('grouplist'))
        ]

    def get_page_text(self) -> str:
        return f'Hey {self.user.username}, this is {self.group.name} group PAGE'


class HomeworkPage(AbsMenuPage):
    state = states.BotPagesStates.HOMEWORK
    urlpath = 'homework'

    def get_items(self) -> list[MenuItem]:
        self.group = App.get().db.get_group(self.query_data['group'])
        return [MenuItem('назад', TransferAction('group', {'group': self.group.id}))]

    def get_page_text(self) -> str:
        return f'Hey {self.user.username}, this is {self.group.name} homework PAGE'
