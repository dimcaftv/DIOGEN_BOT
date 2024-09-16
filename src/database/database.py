from dataclasses import asdict

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from telebot import StatePickleStorage, StateStorageBase

import settings
from . import models


class PrivateChatStorageAdapter:
    def __init__(self, storage: StateStorageBase):
        self.storage = storage

    def set_default_state(self, user_id):
        if self.storage.get_data(user_id, user_id) is None:
            self.storage.set_state(user_id, user_id, 0)
        with self.get_cnt_mng_data(user_id) as data:
            data.setdefault('page_url', 'main')
            data.setdefault('asker_url', '')
            data.setdefault('menu_msg_id', 0)

    def set_data(self, user_id, key, value):
        if self.get_data(user_id, key) != value:
            self.storage.set_data(user_id, user_id, key, value)

    def get_data(self, user_id, key):
        return self.get_user_data(user_id).get(key)

    def get_user_data(self, user_id):
        return self.storage.get_data(user_id, user_id)

    def get_cnt_mng_data(self, user_id):
        return self.storage.get_interactive_data(user_id, user_id)


class UserDataManager:
    def __init__(self, storage: StateStorageBase):
        self.storage = PrivateChatStorageAdapter(storage)

    def get_user(self, user_id: int):
        data = self.storage.get_user_data(user_id)
        return models.UserDataclass(*[data[k] for k in models.UserDataclass.get_keys()])

    def save_user(self, user_id: int, user: models.UserDataclass):
        with self.storage.get_cnt_mng_data(user_id) as data:
            data.update(asdict(user))

    def get_by_key(self, user_id: int, key: str):
        return self.storage.get_data(user_id, key)

    def set_by_key(self, user_id: int, key: str, val):
        self.storage.set_data(user_id, key, val)


class SQLDatabaseManager:
    def __init__(self):
        self.engine = sqlalchemy.create_engine(f'{settings.DB_FULL_PATH}', echo=settings.DEBUG)
        self.sm = sessionmaker(self.engine)
        self.selecting_session = self.sm()

        models.AbstractModel.metadata.create_all(self.engine)

    def exec(self, stmt):
        return self.selecting_session.scalars(stmt)


class DatabaseInterface:
    def __init__(self, storage_path: str):
        self.db = SQLDatabaseManager()
        self.dynamic_user_data = UserDataManager(StatePickleStorage(storage_path))

    @property
    def selecting_session(self):
        return self.db.selecting_session

    def commit(self):
        self.selecting_session.commit()

    def exec(self, stmt):
        return self.db.exec(stmt)

    def save(self, obj: models.AbstractModel):
        self.selecting_session.merge(obj)
        self.selecting_session.commit()

    def delete(self, obj: models.AbstractModel):
        self.selecting_session.delete(obj)
        self.selecting_session.commit()

    @property
    def cnt_mng(self):
        return self.db.sm.begin()
