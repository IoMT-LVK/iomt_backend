from flask_mongoengine import MongoEngine
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = MongoEngine()

class Users(db.Document):
    """User accounts"""
    user_id = db.IntField()
    login = db.StringField()
    password_hash = db.StringField()
    email = db.StringField()

    @property
    def password(self):
        raise AttributeError("Вам не нужно знать пароль!")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def password_valid(self, password):

        return check_password_hash(self.password_hash, password)


class Info(db.Document):
    user_id = db.IntField()
    name = db.StringField()
    surname = db.StringField()
    patronymic = db.StringField()
    birth_date = db.StringField()
    weight = db.FloatField()
    height = db.IntField()
    phone_number = db.StringField()

class Operators(db.Document, UserMixin):
    """Operator accounts"""
    login = db.StringField()
    password_hash = db.StringField()

    @property
    def password(self):
        raise AttributeError("Вам не нужно знать пароль!")

    @password.setter
    def password(self, password):
        self.password = generate_password_hash(password)

    def password_valid(self, password):
        return check_password_hash(self.password, password)


class Devices(db.Document):
    """Devices and their sensors"""
    device_type = db.StringField()
    create_str = db.StringField()

class Userdevices(db.Document):
    """User registered devices"""
    user_id = db.StringField()
    device_name = db.StringField()
    device_id = db.StringField()
    device_type = db.StringField()




