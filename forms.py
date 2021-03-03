from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField, SelectField, SelectMultipleField, PasswordField
from wtforms.validators import DataRequired

class UserData(FlaskForm):
    date_begin = StringField('Дата начала', [DataRequired(message="Введите дату начала")])
    date_end = StringField('Дата конца', [DataRequired(message="Введите дату конца")])
    params = SelectMultipleField('Параметры', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Получить данные')


class AddUser(FlaskForm):
    login = StringField('Логин', [DataRequired(message="Введите имя")])
    password = StringField('Пароль', [DataRequired(message="Введите пароль")])
    name = StringField('Имя', [DataRequired(message="Введите имя")])
    surname = StringField('Фамилия', [DataRequired(message="Введите фамилию")])
    patronymic = StringField('Отчество',[DataRequired(message="Введите отчество")])
    age = StringField('Дата рождения', [DataRequired(message="Введите возраст")])
    weight = FloatField('Вес', [DataRequired(message="Введите вес")])
    height = IntegerField('Рост', [DataRequired(message="Введите рост")])
    phone_number = StringField('Номер телефона', [DataRequired(message="Введите номер телефона")])
    email = StringField('Email', [DataRequired(message="Введите email")])
    submit = SubmitField('Добавить')


class UserList(FlaskForm):
    us_list = SelectField('Пользователь:', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Выбрать')

class LoginForm(FlaskForm):
    username = StringField('Логин', [DataRequired(message="Введите имя")])
    password = PasswordField('Пароль', [DataRequired(message="Введите пароль")])
    submit = SubmitField('Войти')