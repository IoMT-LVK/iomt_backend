from flask_mongoengine import MongoEngine
from werkzeug.security import generate_password_hash, check_password_hash

db = MongoEngine()

class Users(db.Document):

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




