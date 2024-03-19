from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField, SelectField, SelectMultipleField, PasswordField, \
    TextAreaField, BooleanField
from wtforms.validators import DataRequired
from wtforms import widgets


class UserData(FlaskForm):
    device = SelectField('Устройство:', validators=[DataRequired()])
    date_begin = StringField('Дата начала', [DataRequired(message="Введите дату начала")])
    date_end = StringField('Дата конца', [DataRequired(message="Введите дату конца")])
    # params = SelectMultipleField('Параметры', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Получить данные')


class AddUser(FlaskForm):
    login = StringField('Логин', [DataRequired(message="Введите имя")])
    password = StringField('Пароль', [DataRequired(message="Введите пароль")])
    name = StringField('Имя', [DataRequired(message="Введите имя")])
    surname = StringField('Фамилия', [DataRequired(message="Введите фамилию")])
    patronymic = StringField('Отчество', [DataRequired(message="Введите отчество")])
    age = StringField('Дата рождения', [DataRequired(message="Введите возраст")])
    weight = FloatField('Вес', [DataRequired(message="Введите вес")])
    height = IntegerField('Рост', [DataRequired(message="Введите рост")])
    phone_number = StringField('Номер телефона', [DataRequired(message="Введите номер телефона")])
    email = StringField('Email', [DataRequired(message="Введите email")])
    submit = SubmitField('Добавить')


class UserList(FlaskForm):
    us_list = SelectField('Пользователь:', validators=[DataRequired()])
    submit = SubmitField('Выбрать')


class LoginForm(FlaskForm):
    username = StringField('Логин', [DataRequired(message="Введите имя")])
    password = PasswordField('Пароль', [DataRequired(message="Введите пароль")])
    submit = SubmitField('Войти')


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(html_tag='ul', prefix_label=False)
    option_widget = widgets.CheckboxInput()


class AddDevice(FlaskForm):
    name = StringField('Имя устройства', [DataRequired(message="Введите имя устройства")])
    tp = StringField('Тип устройства', [DataRequired(message="Введите тип устройства")])
    chars = MultiCheckboxField('Характеристики')
    submit = SubmitField('Добавить устройство')


class AddCharacteristic(FlaskForm):
    slug = StringField('slug', [DataRequired(message="Введите slug")])
    name = StringField('Имя характеристики', [DataRequired(message="Введите имя характеристики")])
    sid = StringField('Service uuid:', [DataRequired(message="Введите service uuid")])
    cid = StringField('Characteristic uuid:', [DataRequired(message="Введите characteristic uuid")])
    submit = SubmitField('Добавить характеристику')


class AddOperator(FlaskForm):
    login = StringField('Логин', [DataRequired(message="Введите логин")])
    password = StringField('Пароль', [DataRequired(message="Введите пароль")])
    is_admin = BooleanField('Администратор')
    submit = SubmitField('Добавить')