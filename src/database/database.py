import sqlalchemy
from sqlalchemy.orm import Session

import settings
from . import models


class SQLDatabaseManager:
    def __init__(self):
        self.engine = sqlalchemy.create_engine(f'sqlite+pysqlite:///{settings.DB_FULL_PATH}', echo=settings.DEBUG)
        self.session = Session(self.engine)
        models.AbstractModel.metadata.create_all(self.engine)

    def exec(self, stmt):
        return self.session.scalars(stmt)


class DatabaseInterface:
    def __init__(self):
        self.db = SQLDatabaseManager()

    @property
    def session(self):
        return self.db.session

    def commit(self):
        self.session.commit()

    def exec(self, stmt):
        return self.db.exec(stmt)

    def save(self, obj: models.AbstractModel):
        self.session.merge(obj)
        self.session.commit()

    def delete(self, obj: models.AbstractModel):
        self.session.delete(obj)
        self.session.commit()
