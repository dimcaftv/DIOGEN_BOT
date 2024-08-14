from enum import StrEnum


class BotDataKeys(StrEnum):
    MENU_MSG_ID = 'menu_msg_id'
    GROUPS = 'groups'
    PAGE_CB_DATA = 'page_cb_data'
    ASKER = 'asker'


class Singleton(type):
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]
