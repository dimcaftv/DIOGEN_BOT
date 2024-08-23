from app import App
from . import database


def set_app_db():
    App.get().set_db(database.DatabaseInterface())
