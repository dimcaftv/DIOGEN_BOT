from enum import StrEnum

from app import App


class BotDataKeys(StrEnum):
    MENU_MSG_ID = 'menu_msg_id'
    GROUPS = 'groups'
    PAGE_URL = 'page_url'
    ASKER_URL = 'asker'
    INVITE_LINKS = 'invite_links'


def get_user_from_id(user_id):
    return App.get().bot.get_chat_member(user_id, user_id).user
