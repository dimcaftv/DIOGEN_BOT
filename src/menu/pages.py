from datetime import date

from database import models
from messages import messages
from utils.calendar import Week
from .actions.actions import (CopyPrevTimetableAction, FlipNotifyAction, TransferAction,
                              ViewRecentHomeworkAction)
from .actions.ask_actions import (ChangeGroupAdminAction, ChangeNotifyTemplateAction,
                                  CreateGroupAction, CreateInviteAction,
                                  CreateTimetableAction,
                                  DeleteGroupAction, JoinGroupAction,
                                  KickUserAction, RequestAnswerAction, ViewHomeworkAction)
from .menu import AbsMenuPage, KeyboardLayout, MenuItem


class MainPage(AbsMenuPage):
    def get_items(self) -> KeyboardLayout:
        return KeyboardLayout(
                MenuItem('группы', TransferAction('grouplist'))
        )

    def get_page_text(self) -> str:
        return f'Главное меню'


class GroupListPage(AbsMenuPage):
    async def post_init(self):
        self.groups = (await models.UserModel.get(self.user_id)).groups

    def get_items(self) -> KeyboardLayout:
        return KeyboardLayout(
                (MenuItem(g.name, TransferAction('group', {'group': g.id}))
                 for g in self.groups),
                (
                    MenuItem('💾 создать', CreateGroupAction()),
                    MenuItem('🔍 присоединиться', JoinGroupAction())
                ),
                MenuItem('◀ назад', TransferAction('main'))
        )

    def get_page_text(self) -> str:
        return f'Твои группы:\n' + '\n'.join(g.name for g in self.groups)


class GroupPage(AbsMenuPage):
    async def post_init(self):
        self.group = await models.GroupModel.get(self.query_data['group'])

    def get_items(self) -> KeyboardLayout:
        is_admin = self.group.is_group_admin(self.user_id)
        group_id = self.group.id

        return KeyboardLayout(
                (
                    MenuItem('📆 расписание', TransferAction('timetable', {'group': group_id})),
                    MenuItem('🚹 участники', TransferAction('users_list', {'group': group_id}))
                ),
                MenuItem('💥 ответы на сегодня-завтра 💥', ViewRecentHomeworkAction(group_id)),
                MenuItem('🎫 Приглашения', TransferAction('group_invites', {'group': group_id}), True),
                MenuItem('⚙️ Настройки', TransferAction('group_settings', {'group': group_id}), True),
                MenuItem('❌ удалить', DeleteGroupAction(group_id), True),
                MenuItem('◀ назад', TransferAction('grouplist')),
                is_admin=is_admin
        )

    def get_page_text(self) -> str:
        return f'Группа {self.group.name}'


class TimetablePage(AbsMenuPage):
    async def post_init(self):
        self.group = await models.GroupModel.get(self.query_data['group'])
        self.week = Week.from_str(self.query_data['week']) if 'week' in self.query_data else Week.today()

    def get_items(self) -> KeyboardLayout:
        is_admin = self.group.is_group_admin(self.user_id)
        group_id = self.group.id

        return KeyboardLayout(
                (
                    MenuItem('◀', TransferAction('timetable', {'group': group_id, 'week': str(self.week.prev())})),
                    MenuItem('▶', TransferAction('timetable', {'group': group_id, 'week': str(self.week.next())}))
                ),
                (MenuItem(Week.standart_day_format(d),
                          TransferAction('daypage', {'group': group_id, 'date': str(d)}))
                 for d in self.week),
                MenuItem.empty(),
                MenuItem('💾 добавить на эту неделю', CreateTimetableAction(group_id, self.week), True),
                MenuItem('🔄 копировать с прошлой недели', CopyPrevTimetableAction(group_id, self.week), True),
                MenuItem('◀ назад', TransferAction('group', {'group': group_id})),
                is_admin=is_admin
        )

    def get_page_text(self) -> str:
        return f'Расписание группы {self.group.name}'


class DayPage(AbsMenuPage):
    async def post_init(self):
        self.group = await models.GroupModel.get(self.query_data['group'])
        self.date = date.fromisoformat(self.query_data['date'])
        self.lessons = (await models.LessonModel.select(models.LessonModel.date == self.date,
                                                        models.LessonModel.group_id == self.group.id)).all()

    def get_items(self) -> KeyboardLayout:
        return KeyboardLayout(
                (MenuItem(i.name + ' ✅' * bool(i.solutions),
                          ViewHomeworkAction(i.id))
                 for i in self.lessons),
                MenuItem.empty(),
                MenuItem('🥺 Попросить дз', RequestAnswerAction(self.group.id, self.date), visible=bool(self.lessons)),
                MenuItem('◀ назад',
                         TransferAction('timetable',
                                        {'group': self.group.id, 'week': str(Week.from_day(self.date))}))
        )

    def get_page_text(self) -> str:
        return f'Уроки на {Week.standart_day_format(self.date)}:'


class UsersListPage(AbsMenuPage):
    async def post_init(self):
        self.group = await models.GroupModel.get(self.query_data['group'])

    def get_items(self) -> KeyboardLayout:
        is_admin = self.group.is_group_admin(self.user_id)

        return KeyboardLayout(
                MenuItem('☠ кикнуть', KickUserAction(self.group.id), True),
                MenuItem('◀ назад', TransferAction('group', {'group': self.group.id})),
                is_admin=is_admin
        )

    def get_page_text(self) -> str:
        return (f'Участники {self.group.name}, #{len(self.group.members)}:\n' +
                ', '.join((u.username or str(u.id)) for u in self.group.members))


class GroupSettingsPage(AbsMenuPage):
    async def post_init(self):
        self.settings = await models.GroupSettings.get(self.query_data['group'])

    def get_items(self) -> KeyboardLayout:
        return KeyboardLayout(
                MenuItem('Передать админку', ChangeGroupAdminAction(self.settings.group_id)),
                MenuItem(f'Уведомления о новых ответах {["❌", "✅"][self.settings.new_answer_notify]}',
                         FlipNotifyAction(self.settings.group_id)),
                MenuItem('Изменить шаблон уведомления', ChangeNotifyTemplateAction(self.settings.group_id)),
                MenuItem('◀ назад', TransferAction('group', {'group': self.settings.group_id}))
        )

    def get_page_text(self) -> str:
        return (f'Настройки группы {self.settings.group.name}:\n'
                f'Добавлен в общий чат: {["❌", "✅"][bool(self.settings.general_group_chat_id)]}\n'
                f'Шаблон уведомления о новом ответе:\n\n'
                f'"{self.settings.answer_notify_template or messages.default_notify_template}"')


class GroupInvitesPage(AbsMenuPage):
    async def post_init(self):
        self.group = await models.GroupModel.get(self.query_data['group'])

    def get_items(self) -> KeyboardLayout:
        group_id = self.group.id
        is_admin = self.group.is_group_admin(self.user_id)

        return KeyboardLayout(
                MenuItem('💾 создать приглашение', CreateInviteAction(group_id), True),
                MenuItem('🎟 Активные приглашения', TransferAction('active_invites', {'group': group_id}), True),
                MenuItem('◀ назад', TransferAction('group', {'group': self.group.id})),
                is_admin=is_admin
        )

    def get_page_text(self) -> str:
        return f'Настройка приглашений для группы {self.group.name}'


class ActiveInvitesPage(AbsMenuPage):
    async def post_init(self):
        self.group = await models.GroupModel.get(self.query_data['group'])

    def get_items(self) -> KeyboardLayout:
        return KeyboardLayout(
                MenuItem('◀ назад', TransferAction('group_invites', {'group': self.group.id}))
        )

    def get_page_text(self) -> str:
        return (f'Приглашения для группы {self.group.name}:\n' +
                '\n'.join(f'{i.link} - Осталось использований: {i.remain_uses}'
                          for i in self.group.invites))
