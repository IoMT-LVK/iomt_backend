from flask_mongoengine import MongoEngine
from werkzeug.security import generate_password_hash, check_password_hash

db = MongoEngine()

class Users(db.Document):
    """User accounts"""
    user_id = db.IntField()
    login = db.StringField()
    password_hash = db.StringField()
    name = db.StringField()
    surname = db.StringField()
    patronymic = db.StringField()
    birth_date = db.StringField()
    weight = db.FloatField()
    height = db.IntField()
    phone_number = db.StringField()
    email = db.StringField()

    @property
    def password(self):
        raise AttributeError("Вам не нужно знать пароль!")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def password_valid(self, password):
        return check_password_hash(self.password_hash, password)


class Operators(db.Document):
    """Operator accounts"""
    login = db.StringField()
    password_hash = db.StringField()

    @property
    def password(self):
        raise AttributeError("Вам не нужно знать пароль!")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def password_valid(self, password):
        return check_password_hash(self.password_hash, password)


class Devices(db.Document):
    """Devices and their sensors"""
    device = db.StringField()
    sensor = db.StringField()
    sensor_name = db.StringField()
    # TODO: информация о датчиках

class Registerdevices(db.Document):
    """User registered devices"""
    user = db.StringField()
    device = db.StringField()
    device_id = db.StringField()
    sensors = db.StringField()




