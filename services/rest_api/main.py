#-*- coding: utf-8 -*-
from collections import namedtuple
from connexion import App
from connexion.resolver import MethodViewResolver
from peewee import (
    DoesNotExist, 
)

from exceptions import (
    BaseApiError,
    error_handler,
)
from models.base import db_wrapper
from models.user import User
from models.operator import Operator
# from utils import SerializeJSONEncoder
import dev_settings as settings
    
app = App(__name__, specification_dir='openapi/')
app.add_api('openapi.yaml', resolver=MethodViewResolver('views'))
app.add_error_handler(DoesNotExist, error_handler)
app.add_error_handler(BaseApiError, error_handler)

flask_app = app.app
flask_app.config.from_object('dev_settings')
flask_app.config.from_envvar('FLASK_SETTINGS', silent=True)
# flask_app.json_encoder = SerializeJSONEncoder
settings.init_app(flask_app)


db_wrapper.init_app(flask_app)
db_wrapper.database.create_tables([
    User, 
    Operator,
    User.allowed.get_through_model(),
])

if __name__ == "__main__":
    app.run()
