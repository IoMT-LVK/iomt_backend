from peewee import (
    Model,
)
from playhouse.flask_utils import FlaskDB

db_wrapper = FlaskDB()
db = db_wrapper.database
BaseModel = db_wrapper.Model
