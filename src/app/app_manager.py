from utils.singleton import Singleton


class AppManager(metaclass=Singleton):
    def __init__(self, app):
        self.app = app

    @classmethod
    def get_bot(cls):
        return cls().app.bot

    @classmethod
    def get_menu(cls):
        return cls().app.menu

    @classmethod
    def get_db(cls):
        return cls().app.db
