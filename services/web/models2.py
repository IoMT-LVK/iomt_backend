import sqlalchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import services.rest_api.settings as settings
from playhouse.pool import PooledMySQLDatabase
from playhouse.reflection import generate_models
import logging

db = PooledMySQLDatabase(
    database=settings.DB_NAME,
    host=settings.DB_HOST,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    stale_timeout=settings.DB_STALE_TIMEOUT,
)

api_models = generate_models()
globals().update(api_models)
logging.info(f"====================== {api_models} =================")

class User(user):

    @property
    def password(self):
        raise AttributeError("Вам не нужно знать пароль!")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def password_valid(self, password):
        return check_password_hash(self.password_hash, password)


class Operator(operator, UserMixin):

    @property
    def password(self):
        raise AttributeError("Вам не нужно знать пароль!")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def password_valid(self, password):
        return check_password_hash(self.password_hash, password)


class Admins(Operator):
    """Administrators of project, can be created directly from command line"""
    pass

class Characteristic(characteristic):
    """Some characteristics of a device"""
    pass


class Device(device):
    """Model, specifying device and pinning it to user"""
    pass


class DeviceType(device_type):
    """Descriptions of devices"""
    pass




