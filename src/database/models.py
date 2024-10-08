import dataclasses
from datetime import date
from typing import Self

from sqlalchemy import BigInteger, Date, ForeignKey, delete, select
from sqlalchemy.orm import Mapped, as_declarative, mapped_column, relationship

from app.app_manager import AppManager
from utils import utils


@dataclasses.dataclass
class UserDataclass:
    page_url: str = 'main'
    asker_url: str = ''
    menu_msg_id: int = 0
    sent_hw: bool = False

    @classmethod
    async def get_user(cls, user_id) -> Self:
        return await AppManager.get_db().dynamic_user_data.get_user(user_id)

    async def save(self, user_id):
        await AppManager.get_db().dynamic_user_data.save_user(user_id, self)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        AppManager.get_db().dynamic_user_data.save_all_data()


@as_declarative()
class AbstractModel:
    __tablename__ = ''

    async def save(self):
        await AppManager.get_db().save(self)

    async def delete(self):
        await AppManager.get_db().delete(self)

    @classmethod
    async def get(cls, *pks, session=None) -> Self:
        if session is None:
            session = AppManager.get_db().selecting_session
        return await session.get(cls, pks)

    @classmethod
    async def select(cls, *where, session=None):
        if session is None:
            session = AppManager.get_db().selecting_session
        return await session.scalars(select(cls).where(*where))

    @classmethod
    async def delete_where(cls, *where, session=None):
        await session.execute(delete(cls).where(*where))


class UserModel(AbstractModel):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(nullable=True)
    fav_group_id: Mapped[int] = mapped_column(nullable=True)

    admin_in: Mapped[list['GroupModel']] = relationship(back_populates='admin', uselist=True)
    groups: Mapped[list['GroupModel']] = relationship(back_populates='members', uselist=True, secondary="user_to_group",
                                                      lazy='selectin')
    solutions: Mapped[list['SolutionModel']] = relationship(back_populates='author', uselist=True)

    async def get_tg_user(self):
        return await utils.get_tg_user(self.id)


class GroupModel(AbstractModel):
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    admin: Mapped['UserModel'] = relationship(back_populates='admin_in', uselist=False)
    admin_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    members: Mapped[list['UserModel']] = relationship(back_populates='groups', uselist=True, secondary="user_to_group",
                                                      lazy='selectin')
    invites: Mapped[list['GroupInviteModel']] = relationship(back_populates='group', uselist=True,
                                                             cascade='save-update,merge,delete,delete-orphan',
                                                             lazy='selectin')
    lessons: Mapped[list['LessonModel']] = relationship(back_populates='group', uselist=True,
                                                        cascade='save-update,merge,delete,delete-orphan')

    settings: Mapped['GroupSettings'] = relationship(back_populates='group', uselist=False,
                                                     cascade='save-update,merge,delete,delete-orphan',
                                                     lazy='selectin')

    def is_group_admin(self, user_id: int) -> bool:
        return self.admin_id == user_id


class UserToGroupModel(AbstractModel):
    __tablename__ = 'user_to_group'

    user_fk: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    group_fk: Mapped[int] = mapped_column(ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True)


class GroupInviteModel(AbstractModel):
    __tablename__ = 'group_invites'

    link: Mapped[str] = mapped_column(primary_key=True)

    group: Mapped['GroupModel'] = relationship(back_populates='invites', uselist=False, lazy='selectin')
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)

    remain_uses: Mapped[int] = mapped_column(default=1)


class LessonModel(AbstractModel):
    __tablename__ = 'lessons'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    date: Mapped[date] = mapped_column(Date)

    group: Mapped['GroupModel'] = relationship(back_populates='lessons', uselist=False)
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)

    name: Mapped[str] = mapped_column(nullable=False)
    notes: Mapped[str] = mapped_column(nullable=True)

    solutions: Mapped[list['SolutionModel']] = relationship(back_populates='lesson', uselist=True,
                                                            cascade='save-update,merge,delete,delete-orphan',
                                                            lazy='selectin')


class SolutionModel(AbstractModel):
    __tablename__ = 'solutions'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    lesson: Mapped['LessonModel'] = relationship(back_populates='solutions', uselist=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False)

    msg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    author: Mapped['UserModel'] = relationship(back_populates='solutions', uselist=False)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created: Mapped[date] = mapped_column(Date)

    file_id: Mapped[str] = mapped_column(nullable=True)


class GroupSettings(AbstractModel):
    __tablename__ = 'group_settings'

    group: Mapped['GroupModel'] = relationship(back_populates='settings', uselist=False, lazy='selectin')
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True)

    general_group_chat_id: Mapped[int] = mapped_column(nullable=True)
    new_answer_notify: Mapped[bool] = mapped_column(default=False)
    answer_notify_template: Mapped[str] = mapped_column(nullable=True)
