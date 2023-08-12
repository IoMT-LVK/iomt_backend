#-*- coding: utf-8 -*-
"""
Main run file for REST

Contain `app` variable which you need pass to ASGI app (uvicorn)
"""

from connexion import App
from connexion.resolver import MethodViewResolver
import peewee
import logging
import time

from exceptions import (
    BaseApiError,
    error_handler,
)
from exceptions import init_app as exceptions_init_app
from models.base import db
from models.characteristic import Characteristic
from models import (
    User,
    Operator,
    Device,
    DeviceType,
)
import dev_settings as settings
    
app = App(__name__, specification_dir='openapi/')
app.add_api('openapi.yaml', resolver=MethodViewResolver('views'))
exceptions_init_app(app)
app.add_error_handler(BaseApiError, error_handler)

flask_app = app.app
flask_app.config.from_object('dev_settings')
flask_app.config.from_envvar('FLASK_SETTINGS', silent=True)
settings.init_app(flask_app)

log = logging.getLogger(__name__)
peewee_logger = logging.getLogger('peewee')
peewee_logger.addHandler(logging.StreamHandler())
peewee_logger.setLevel(logging.DEBUG)

@flask_app.before_request
def db_connect():
    db.connect(reuse_if_open=True)

@flask_app.teardown_request
def db_disconnect(exc):
    if not db.is_closed():
        db.close()
    
db.create_tables([
    User, 
    Operator,
    User.allowed.get_through_model(),
    Device,
    DeviceType,
    DeviceType.characteristics.get_through_model(),
    Characteristic,
])
if not db.is_closed():
    db.close()

if __name__ == "__main__":
    app.run()
