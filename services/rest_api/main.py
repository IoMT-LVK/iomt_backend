#-*- coding: utf-8 -*-
"""
Main run file for REST

Contain `app` variable which you need pass to ASGI app (uvicorn)
"""

from connexion import App
from connexion.resolver import MethodViewResolver

from exceptions import (
    BaseApiError,
    error_handler,
)
from exceptions import init_app as exceptions_init_app
from models.base import db_wrapper
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

@flask_app.before_request
def tt():
  flask_app.logger.debug(f"br {db_wrapper.database.is_closed()=}")
    
db_wrapper.init_app(flask_app)
@flask_app.before_request
def t():
  flask_app.logger.debug(f"br2 {db_wrapper.database.is_closed()=}")
    
import logging
flask_app.logger.setLevel(logging.DEBUG)

@flask_app.teardown_request
def teardown_request(r):
  if not db_wrapper.database.is_closed():
      db_wrapper.database.close()

db_wrapper.database.create_tables([
    User, 
    Operator,
    User.allowed.get_through_model(),
    Device,
    DeviceType,
    DeviceType.characteristics.get_through_model(),
    Characteristic,
])

if __name__ == "__main__":
    app.run()
