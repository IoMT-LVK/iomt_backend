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
from utils import hash_password
import dev_settings as settings
    
app = App(__name__, specification_dir='openapi/')
app.add_api('openapi.yaml', resolver=MethodViewResolver('views'))
exceptions_init_app(app)
app.add_error_handler(BaseApiError, error_handler)

flask_app = app.app
flask_app.config.from_object('dev_settings')

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)
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
    
try_num = 0
while try_num < settings.DB_CONNECTION_RETRY_COUNT:
    try:
        db.connect()
        break
    except peewee.OperationalError:
        try_num += 1
        log.warning(f"Can't connect to db. Retry number {try_num}. Sleep for {2**try_num} seconds.")
        time.sleep(2**try_num)
else:
    log.error("Can't connect to database")
    exit(1)

db.create_tables([
    User, 
    Operator,
    User.allowed.get_through_model(),
    Device,
    DeviceType,
    DeviceType.characteristics.get_through_model(),
    Characteristic,
])
passw_hash, salt = hash_password(settings.ROOT_OP_PASSWORD)
try:
    Operator.create(
        login=settings.ROOT_OP_LOGIN,
        password_hash=passw_hash,
        salt=salt,
        is_admin=True,
    )
    log.debug("Root operator created")
except peewee.IntegrityError:
    log.debug("Root operator exist")

if not db.is_closed():
    db.close()

if __name__ == "__main__":
    app.run()
