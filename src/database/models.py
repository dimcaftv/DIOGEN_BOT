from datetime import date
from typing import Self

from sqlalchemy import BigInteger, Date, ForeignKey, delete, select
from sqlalchemy.orm import Mapped, as_declarative, mapped_column, relationship

from app.app_manager import AppManager


@as_declarative()
class AbstractModel:
    __tablename__ = ''

    def save(self):
        AppManager.get_db().save(self)

    def delete(self):
        AppManager.get_db().delete(self)

    @classmethod
    def get(cls, *pks) -> Self:
        return AppManager.get_db().session.get(cls, tuple(pks))

    @classmethod
    def select(cls, *where):
        return AppManager.get_db().exec(select(cls).where(*where))

    @classmethod
    def delete_where(cls, *where):
        AppManager.get_db().session.execute(delete(cls).where(*where))


class UserModel(AbstractModel):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column()
    page_url: Mapped[str] = mapped_column(default='main')
    asker_url: Mapped[str] = mapped_column(nullable=True)
    menu_msg_id: Mapped[int] = mapped_column(BigInteger)
    fav_group_id: Mapped[int] = mapped_column(nullable=True)

    admin_in: Mapped[list['GroupModel']] = relationship(back_populates='admin', uselist=True)
    groups: Mapped[list['GroupModel']] = relationship(back_populates='members', uselist=True, secondary="user_to_group")
    solutions: Mapped[list['SolutionModel']] = relationship(back_populates='author', uselist=True)


class GroupModel(AbstractModel):
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    admin: Mapped['UserModel'] = relationship(back_populates='admin_in', uselist=False)
    admin_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    members: Mapped[list['UserModel']] = relationship(back_populates='groups', uselist=True, secondary="user_to_group")
    invites: Mapped[list['GroupInviteModel']] = relationship(back_populates='group', uselist=True)
    lessons: Mapped[list['LessonModel']] = relationship(back_populates='group', uselist=True)


class UserToGroupModel(AbstractModel):
    __tablename__ = 'user_to_group'

    user_fk: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    group_fk: Mapped[int] = mapped_column(ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True)


class GroupInviteModel(AbstractModel):
    __tablename__ = 'group_invites'

    link: Mapped[str] = mapped_column(primary_key=True)

    group: Mapped['GroupModel'] = relationship(back_populates='invites', uselist=False)
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

    solutions: Mapped[list['SolutionModel']] = relationship(back_populates='lesson', uselist=True)


class SolutionModel(AbstractModel):
    __tablename__ = 'solutions'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    lesson: Mapped['LessonModel'] = relationship(back_populates='solutions', uselist=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False)

    msg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    author: Mapped['UserModel'] = relationship(back_populates='solutions', uselist=False)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    created: Mapped[date] = mapped_column(Date)
