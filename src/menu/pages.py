from database import models
from menu.actions import (CreateGroupAction, CreateInviteAction, DeleteGroupAction, JoinGroupAction, KickUserAction,
                          TransferAction)
from menu.menu import AbsMenuPage, MenuItem
from utils import filters, states, utils


class MainPage(AbsMenuPage):
    state = states.BotPagesStates.MAIN
    urlpath = 'main'

    def get_items(self) -> list[MenuItem]:
        return [
            MenuItem('группы', TransferAction('grouplist'))
        ]

    def get_page_text(self) -> str:
        return f'Hey {self.tg_user.first_name}, this is MAIN PAGE'


class GroupListPage(AbsMenuPage):
    state = states.BotPagesStates.GROUPLIST
    urlpath = 'grouplist'

    def get_items(self) -> list[MenuItem]:
        self.groups = self.user.groups

        groupItems = [
            MenuItem(g.name, TransferAction('group', {'group': g.id}))
            for g in self.groups
        ]

        return groupItems + [
            MenuItem('создать', CreateGroupAction()),
            MenuItem('присоединиться', JoinGroupAction()),
            MenuItem('назад', TransferAction('main'))
        ]

    def get_page_text(self) -> str:
        return f'Hey {self.tg_user.first_name}, this is GROUPLIST PAGE\n' + '\n'.join(
                f'{i}: {g.name}' for i, g in enumerate(self.groups, start=1))


class GroupPage(AbsMenuPage):
    state = states.BotPagesStates.GROUP
    urlpath = 'group'

    def get_items(self) -> list[MenuItem]:
        self.group = models.GroupModel.get(self.query_data['group'])
        is_admin = filters.is_group_admin(self.user.id, self.group.id)
        items = ([
                     MenuItem('дз', TransferAction('homework', {'group': self.group.id})),
                     MenuItem('участники', TransferAction('users_list', {'group': self.group.id}))
                 ] + [
                     MenuItem('создать приглашение', CreateInviteAction(self.group.id)),
                     MenuItem('Активные приглашения', TransferAction('active_invites', {'group': self.group.id})),
                     MenuItem('удалить', DeleteGroupAction(self.group.id))
                 ] * is_admin + [
                     MenuItem('назад', TransferAction('grouplist'))
                 ])

        return items

    def get_page_text(self) -> str:
        return (f'Hey {self.tg_user.first_name}, this is {self.group.name} group PAGE\nusers: ' +
                ', '.join(utils.get_tg_user_from_model(u).first_name for u in self.group.members))


class HomeworkPage(AbsMenuPage):
    state = states.BotPagesStates.HOMEWORK
    urlpath = 'homework'

    def get_items(self) -> list[MenuItem]:
        self.group = models.GroupModel.get(self.query_data['group'])
        return [MenuItem('назад', TransferAction('group', {'group': self.group.id}))]

    def get_page_text(self) -> str:
        return f'Hey {self.tg_user.first_name}, this is {self.group.name} homework PAGE'


class UsersListPage(AbsMenuPage):
    state = states.BotPagesStates.USERSLIST
    urlpath = 'users_list'

    def get_items(self) -> list[MenuItem]:
        self.group = models.GroupModel.get(self.query_data['group'])
        is_admin = filters.is_group_admin(self.user.id, self.group.id)
        items = ([MenuItem('кикнуть', KickUserAction(self.group.id))] * is_admin +
                 [MenuItem('назад', TransferAction('group', {'group': self.group.id}))])
        return items

    def get_page_text(self) -> str:
        return (f'Hey {self.tg_user.first_name}, this is {self.group.name} userlist PAGE\nusers: ' +
                ', '.join(utils.get_tg_user_from_model(u).first_name for u in self.group.members))


class ActiveInvitesPage(AbsMenuPage):
    state = states.BotPagesStates.ACTIVE_INVITES
    urlpath = 'active_invites'

    def get_items(self) -> list[MenuItem]:
        self.group = models.GroupModel.get(self.query_data['group'])
        return [MenuItem('назад', TransferAction('group', {'group': self.group.id}))]

    def get_page_text(self) -> str:
        return (f'Hey {self.tg_user.first_name}, this is {self.group.name} invites PAGE\ninvites: ' +
                '\n'.join(f'{i.link} - Осталось использований: {i.remain_uses}'
                          for i in models.GroupModel.get(self.group.id).invites))
