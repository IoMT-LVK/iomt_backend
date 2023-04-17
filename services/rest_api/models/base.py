from playhouse.flask_utils import FlaskDB

db_wrapper = FlaskDB()
db = db_wrapper.database
BaseModel = db_wrapper.Model

class BaseModel(db_wrapper.Model):
    _do_not_serialize = []

    def serialize(self):
        return {name: val for name, val in self.__data__.items() if name not in self._do_not_serialize}
