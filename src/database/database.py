import sqlalchemy
from sqlalchemy.orm import Session, sessionmaker

import settings
from . import models


class SQLDatabaseManager:
    def __init__(self):
        self.engine = sqlalchemy.create_engine(f'{settings.DB_FULL_PATH}', echo=settings.DEBUG)
        self.sm = sessionmaker(self.engine)
        self.selecting_session = self.sm()
        Session()

        models.AbstractModel.metadata.create_all(self.engine)

    def exec(self, stmt):
        return self.selecting_session.scalars(stmt)


class DatabaseInterface:
    def __init__(self):
        self.db = SQLDatabaseManager()

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
