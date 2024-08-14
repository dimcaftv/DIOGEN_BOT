from app import App
from menu import menu, pages

pages_list = [
    pages.MainPage,
    pages.GroupListPage,
    pages.GroupPage,
    pages.HomeworkPage
]


def set_app_menu():
    m = menu.Menu(pages_list)
    App.get().set_menu(m)
