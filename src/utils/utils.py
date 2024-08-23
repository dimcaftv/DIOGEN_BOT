from enum import StrEnum
from uuid import uuid4

from app import App
from database import models


class BotDataKeys(StrEnum):
    MENU_MSG_ID = 'menu_msg_id'
    GROUPS = 'groups'
    PAGE_URL = 'page_url'
    ASKER_URL = 'asker'
    INVITE_LINKS = 'invite_links'


def get_tg_user_from_model(user: models.UserModel):
    return App.get().bot.get_chat_member(user.id, user.id).user


def generate_invite_link():
    links = [i.link for i in models.GroupInviteModel.select().all()]
    while (l := uuid4().hex[:6]) in links:
        continue
    return l
