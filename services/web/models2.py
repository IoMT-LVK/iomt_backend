from flask_login import UserMixin
import settings
from playhouse.pool import PooledMySQLDatabase
from playhouse.reflection import generate_models
from peewee import Model
import logging
from utils import hash_password
from peewee import (
    AutoField,
    CharField,
    UUIDField,
    BlobField,
    IntegerField,
    ManyToManyField,
    DateField,
    BooleanField,
    ForeignKeyField,
    FixedCharField
)

db = PooledMySQLDatabase(
    database=settings.DB_NAME,
    host=settings.DB_HOST,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    stale_timeout=settings.DB_STALE_TIMEOUT,
)
db.connect()

class BaseModel(Model):
    _do_not_serialize = []

    class Meta:
        database = db

logging.basicConfig(level=logging.INFO)

api_models = generate_models(db)
globals().update(api_models)
logging.info(f"====================== {api_models} =================")


class Operator(BaseModel, UserMixin):

    id = AutoField()
    
    login = CharField(
        null=False,
        index=True,
        unique=True,
        max_length=32,
    )
    password_hash = BlobField(null=False)
    salt = BlobField(null=False)
    is_admin = BooleanField(null=False, default=False)

    def get_id(self):
        return self.login

    @property
    def password(self):
        raise AttributeError("Вам не нужно знать пароль!")

    """@password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)"""

    def password_valid(self, password):
        return hash_password(password, self.salt)[0] == self.password_hash


class User(BaseModel):

    login = CharField(
        null=False,
        index=True,
        unique=True,
        max_length=32,
    )
    password_hash = BlobField(null=False)
    salt = BlobField(null=False)

    weight = IntegerField(null=True)
    height = IntegerField(null=True)
    email = CharField(null=False, max_length=320)
    name = CharField(null=False, max_length=32)
    surname = CharField(null=False, max_length=32)
    patronymic = CharField(null=True, max_length=32)
    born = DateField(null=True)
    allowed = ManyToManyField(Operator, 'allowed_users')

    @property
    def password(self):
        raise AttributeError("Вам не нужно знать пароль!")

    def password_valid(self, password):
        return hash_password(password, self.salt)[0] == self.password_hash
    

class Characteristic(BaseModel):
    id = AutoField()

    slug = CharField(
        null=False,
        index=True,
        unique=True,
        max_length=32,
    )
    name = CharField(
        null=False,
        unique=False,
        max_length=48,
    )
    # возможно тут стоило бы использовать UUIDField
    # но на бэке ээто особо не нужно, а в ручках может вызвать
    # неожиданные проблемы сравнения со строкой
    service_uuid = CharField(
        null=False,
        unique=False,
    )
    characteristic_uuid = CharField(
        null=False,
        unique=False,
    )
    

class DeviceType(BaseModel):
    id = AutoField()

    name = CharField(
        null=False,
        index=True,
        unique=True,
        max_length=64,
    )
    name_regex = CharField(
        null=True,
        unique=True,
        max_length=128,
    )
    type = CharField(
        null=False,
        unique=False,
    )
    characteristics = ManyToManyField(Characteristic, 'devices')


class Device(BaseModel):
    id = AutoField()

    user = ForeignKeyField(
        User,
        backref='devices',
        null=False,
        index=True,
    )
    device_type = ForeignKeyField(
        DeviceType,
        backref='users',
        null=False,
    )
    mac = FixedCharField(  # TODO сделать кастомное поле для MAC адресов
        max_length=20,
        null=False,
        unique=False,
    )