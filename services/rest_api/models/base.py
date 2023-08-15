from peewee import Model
from playhouse.flask_utils import FlaskDB
from playhouse.pool import PooledMySQLDatabase

import dev_settings as settings

db = PooledMySQLDatabase(
    database=settings.DB_NAME,
    host=settings.DB_HOST,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    stale_timeout=settings.DB_STALE_TIMEOUT,
)

class BaseModel(Model):
    _do_not_serialize = []

    def serialize(self):
        return {name: val for name, val in self.__data__.items() if name not in self._do_not_serialize}

    class Meta:
        database = db
