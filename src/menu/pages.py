from datetime import date

from database import models
from menu.actions import (AddHomeworkAction, CopyPrevTimetableAction, CreateGroupAction, CreateInviteAction,
                          CreateTimetableAction, DeleteGroupAction, JoinGroupAction, KickUserAction, TransferAction,
                          ViewHomeworkAction, ViewRecentHomeworkAction)
from menu.menu import AbsMenuPage, KeyboardLayout, MenuItem
from utils import states
from utils.calendar import Week


class MainPage(AbsMenuPage):
    state = states.BotPagesStates.MAIN
    urlpath = 'main'

    def get_items(self) -> list[MenuItem]:
        return KeyboardLayout(
                MenuItem('группы', TransferAction('grouplist'))
        )

    def get_page_text(self) -> str:
        return f'Главное меню'


class GroupListPage(AbsMenuPage):
    state = states.BotPagesStates.GROUPLIST
    urlpath = 'grouplist'

    def get_items(self) -> list[MenuItem]:
        self.groups = models.UserModel.get(self.tg_user.id).groups

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
        return f'Список групп:\n' + '\n'.join(g.name for g in self.groups)


class GroupPage(AbsMenuPage):
    state = states.BotPagesStates.GROUP
    urlpath = 'group'

    def get_items(self) -> list[MenuItem]:
        self.group = models.GroupModel.get(self.query_data['group'])
        is_admin = self.group.is_group_admin(self.tg_user.id)
        group_id = self.group.id

        return KeyboardLayout(
                (
                    MenuItem('📆 расписание', TransferAction('timetable', {'group': group_id})),
                    MenuItem('🚹 участники', TransferAction('users_list', {'group': group_id}))
                ),
                MenuItem('💥 ответы на сегодня-завтра 💥', ViewRecentHomeworkAction(group_id)),
                (
                    MenuItem('💾 создать приглашение', CreateInviteAction(group_id), True),
                    MenuItem('🎟 Активные приглашения', TransferAction('active_invites', {'group': group_id}), True),
                ),
                MenuItem('❌ удалить', DeleteGroupAction(group_id), True),
                MenuItem('◀ назад', TransferAction('grouplist')),
                is_admin=is_admin
        )

    def get_page_text(self) -> str:
        return f'Группа {self.group.name}'


class TimetablePage(AbsMenuPage):
    state = states.BotPagesStates.TIMETABLE
    urlpath = 'timetable'

    def get_items(self) -> list[MenuItem]:
        self.group = models.GroupModel.get(self.query_data['group'])
        self.week = Week.from_str(self.query_data['week']) if 'week' in self.query_data else Week.today()

        is_admin = self.group.is_group_admin(self.tg_user.id)
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
    state = states.BotPagesStates.DAY
    urlpath = 'daypage'

    def get_items(self) -> list[MenuItem]:
        self.group = models.GroupModel.get(self.query_data['group'])
        self.date = date.fromisoformat(self.query_data['date'])

        lessons = models.LessonModel.select(models.LessonModel.date == self.date,
                                            models.LessonModel.group_id == self.group.id).all()

        return KeyboardLayout(
                (MenuItem(i.name + ' ✅' * bool(i.solutions),
                          TransferAction('lesson', {'group': self.group.id, 'lesson_id': i.id}))
                 for i in lessons),
                MenuItem.empty(),
                MenuItem('◀ назад',
                         TransferAction('timetable',
                                        {'group': self.group.id, 'week': str(Week.from_day(self.date))}))
        )

    def get_page_text(self) -> str:
        return f'Уроки на {Week.standart_day_format(self.date)}:'


class LessonPage(AbsMenuPage):
    state = states.BotPagesStates.LESSON
    urlpath = 'lesson'

    def get_items(self) -> list[MenuItem]:
        self.lesson = models.LessonModel.get(self.query_data['lesson_id'])

        return KeyboardLayout(
                (
                    MenuItem('🔍 посмотреть', ViewHomeworkAction(self.lesson.id)),
                    MenuItem('💾 добавить', AddHomeworkAction(self.lesson.id))
                ),
                MenuItem('◀ назад',
                         TransferAction('daypage',
                                        {'group': self.lesson.group_id, 'date': str(self.lesson.date)}))
        )

    def get_page_text(self) -> str:
        return (f'"{self.lesson.name}" {Week.standart_day_format(self.lesson.date)}\n' +
                (f'Доп. задание: {self.lesson.notes}' if self.lesson.notes else ''))


class UsersListPage(AbsMenuPage):
    state = states.BotPagesStates.USERSLIST
    urlpath = 'users_list'

    def get_items(self) -> list[MenuItem]:
        self.group = models.GroupModel.get(self.query_data['group'])
        is_admin = self.group.is_group_admin(self.tg_user.id)

        return KeyboardLayout(
                MenuItem('☠ кикнуть', KickUserAction(self.group.id), True),
                MenuItem('◀ назад', TransferAction('group', {'group': self.group.id})),
                is_admin=is_admin
        )

    def get_page_text(self) -> str:
        return (f'Участники {self.group.name}:\n' +
                ', '.join((u.username or str(u.id)) for u in self.group.members))


class ActiveInvitesPage(AbsMenuPage):
    state = states.BotPagesStates.ACTIVE_INVITES
    urlpath = 'active_invites'

    def get_items(self) -> list[MenuItem]:
        self.group = models.GroupModel.get(self.query_data['group'])
        return KeyboardLayout(
                MenuItem('◀ назад', TransferAction('group', {'group': self.group.id}))
        )

    def get_page_text(self) -> str:
        return (f'Приглашения для группы {self.group.name}:\n' +
                '\n'.join(f'{i.link} - Осталось использований: {i.remain_uses}'
                          for i in self.group.invites))
