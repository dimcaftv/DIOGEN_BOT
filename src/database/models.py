from typing import Self

from sqlalchemy import BigInteger, ForeignKey, select
from sqlalchemy.orm import Mapped, as_declarative, mapped_column, relationship

from app.app_manager import AppManager


@as_declarative()
class AbstractModel:
    def save(self):
        AppManager.get_db().save(self)

    def delete(self):
        AppManager.get_db().delete(self)

    @classmethod
    def get(cls, pk) -> Self:
        return AppManager.get_db().get(cls, pk)

    @classmethod
    def select(cls, *where):
        return AppManager.get_db().exec(select(cls).where(*where))


class UserModel(AbstractModel):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    page_url: Mapped[str] = mapped_column(default='main')
    asker_url: Mapped[str] = mapped_column(nullable=True)
    menu_msg_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

    admin_in: Mapped[list['GroupModel']] = relationship(back_populates='admin', uselist=True)
    groups: Mapped[list['GroupModel']] = relationship(back_populates='members', uselist=True, secondary="user_to_group")


class GroupModel(AbstractModel):
    __tablename__ = 'groups'
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    admin: Mapped['UserModel'] = relationship(back_populates='admin_in', uselist=False)
    admin_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    members: Mapped[list['UserModel']] = relationship(back_populates='groups', uselist=True, secondary="user_to_group")
    invites: Mapped[list['GroupInviteModel']] = relationship(back_populates='group', uselist=True)


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
