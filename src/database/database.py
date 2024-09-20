from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from telebot.asyncio_storage import StatePickleStorage, StateStorageBase

import settings
from . import models


class PrivateChatStorageAdapter:
    def __init__(self, storage: StateStorageBase):
        self.storage = storage

    async def set_default_state(self, user_id):
        if await self.storage.get_data(user_id, user_id) is None:
            await self.storage.set_state(user_id, user_id, 0)
        async with self.get_cnt_mng_data(user_id) as data:
            data.setdefault('page_url', 'main')
            data.setdefault('asker_url', '')
            data.setdefault('menu_msg_id', 0)

    async def set_data(self, user_id, key, value):
        if await self.get_data(user_id, key) != value:
            await self.storage.set_data(user_id, user_id, key, value)

    async def get_data(self, user_id, key):
        return (await self.get_user_data(user_id)).get(key)

    async def get_user_data(self, user_id):
        return await self.storage.get_data(user_id, user_id)

    def get_cnt_mng_data(self, user_id):
        return self.storage.get_interactive_data(user_id, user_id)


class UserDataManager:
    def __init__(self, storage: StateStorageBase):
        self.storage = PrivateChatStorageAdapter(storage)

    async def get_user(self, user_id: int):
        data = await self.storage.get_user_data(user_id)
        return models.UserDataclass(*[data[k] for k in models.UserDataclass.get_keys()])

    async def save_user(self, user_id: int, user: models.UserDataclass):
        async with self.storage.get_cnt_mng_data(user_id) as data:
            data.update(asdict(user))

    async def get_by_key(self, user_id: int, key: str):
        return await self.storage.get_data(user_id, key)

    async def set_by_key(self, user_id: int, key: str, val):
        await self.storage.set_data(user_id, key, val)


class SQLDatabaseManager:
    def __init__(self):
        self.engine = create_async_engine(settings.DB_FULL_PATH, echo=settings.DEBUG)
        self.sm = sessionmaker(self.engine, class_=AsyncSession)
        self.selecting_session = self.sm()

    async def create_all_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(models.AbstractModel.metadata.create_all)

    async def exec(self, stmt):
        return await self.selecting_session.scalars(stmt)


class DatabaseInterface:
    def __init__(self, storage_path: str):
        self.db = SQLDatabaseManager()
        self.dynamic_user_data = UserDataManager(StatePickleStorage(storage_path))

    @property
    def selecting_session(self):
        return self.db.selecting_session

    async def commit(self):
        await self.selecting_session.commit()

    async def exec(self, stmt):
        return await self.db.exec(stmt)

    async def save(self, obj: models.AbstractModel):
        await self.selecting_session.merge(obj)
        await self.selecting_session.commit()

    async def delete(self, obj: models.AbstractModel):
        await self.selecting_session.delete(obj)
        await self.selecting_session.commit()

    @property
    def cnt_mng(self):
        return self.db.sm().begin()
