from peewee import Model
from playhouse.flask_utils import FlaskDB
from playhouse.pool import PooledMySQLDatabase

db = PooledMySQLDatabase(
    'IoMT_DB',  # TODO вынести в настройки
    stale_timeout=50,
    host='mysql',
    user='rest',
    password='TODOCHANGE',
)

class BaseModel(Model):
    _do_not_serialize = []

    def serialize(self):
        return {name: val for name, val in self.__data__.items() if name not in self._do_not_serialize}

    class Meta:
        database = db
