from app import App
from menu import actions, menu, pages

pages_list = [
    pages.MainPage,
    pages.GroupListPage,
    pages.GroupPage,
    pages.HomeworkPage
]

actions_list = [
    actions.TransferAction,
    actions.AddGroupAction,
    actions.DeleteGroupAction
]


def set_app_menu():
    m = menu.Menu(pages_list, actions_list)
    App.get().set_menu(m)
