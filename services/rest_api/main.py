#-*- coding: utf-8 -*-
from connexion import App
from connexion.resolver import MethodViewResolver
from peewee import (
    DoesNotExist, 
    MySQLDatabase,
)

from models.base import db_wrapper
from models.user import User
# from models.operator import Operator
from utils import (
    not_found_handler,
    SerializeJSONEncoder,
)
    
app = App(__name__, specification_dir='openapi/')
app.add_api('openapi.yaml', resolver=MethodViewResolver('views'))
app.add_error_handler(DoesNotExist, not_found_handler)

flask_app = app.app
flask_app.json_encoder = SerializeJSONEncoder
flask_app.config.update(
    DATABASE=MySQLDatabase(
        'IoMT_DB', 
        host='mysql',
        user='rest',
        password='TODOCHANGE',
    ),
    FLASKDB_EXCLUDED_ROUTES=tuple(),
)
db_wrapper.init_app(flask_app)
db_wrapper.database.create_tables([User])#, Operator])

if __name__ == "__main__":
    app.run()
