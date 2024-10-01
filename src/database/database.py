from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from telebot.asyncio_storage import StatePickleStorage

import settings
from . import models


class PrivateChatStorageAdapter:
    def __init__(self, storage: StatePickleStorage):
        self.storage = storage

    async def set_default_state(self, user_id):
        if await self.storage.get_data(user_id, user_id) is None:
            await self.storage.set_state(user_id, user_id, 0)
        await self.set_data(user_id, 'user', models.UserDataclass())

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
    def __init__(self, storage: StatePickleStorage):
        self.storage = PrivateChatStorageAdapter(storage)

    async def get_user(self, user_id: int):
        return await self.get_by_key(user_id, 'user')

    async def save_user(self, user_id: int, user: models.UserDataclass):
        await self.set_by_key(user_id, 'user', user)

    async def get_by_key(self, user_id: int, key: str):
        return await self.storage.get_data(user_id, key)

    async def set_by_key(self, user_id: int, key: str, val):
        await self.storage.set_data(user_id, key, val)

    def save_all_data(self):
        self.storage.storage.update_data()


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
        return self.db.sm.begin()
