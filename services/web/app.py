from flask import Flask, render_template, request, redirect, session, send_file, jsonify, url_for

from forms import *
from blueprints.api import get_clickhouse_data
from flask_wtf.csrf import CSRFProtect
from models import  Users, Operators, Devices, Userdevices, Info
from models2 import User, Operator, Device, DeviceType
from werkzeug.security import generate_password_hash
from flask_login import current_user, login_user, login_required, logout_user, LoginManager
import auth
import random
import csv
import uuid
import logging
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from rest_api.utils import encode_token, decode_token, hash_password
import rest_api.settings as settings
from time import time


app = Flask(__name__)

""" Код ниже был до мерджа с докером, возможно он там нужен
app.config['MONGODB_SETTINGS'] = {
    'db': 'data',
    'host': '172.30.7.214'
}
app.config.from_pyfile('config.cfg')

manager = LoginManager(app)
manager.init_app(app)

db.init_app(app)
csrf = CSRFProtect(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
mail = Mail(app)

click_password = "iomtpassword123"
"""

# Initializing logger
gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(gunicorn_error_logger.level)

# Loading configuration
app.config.from_object('default_conf')
config_loaded = app.config.from_envvar('FLASK_CONFIG', silent=True)
if not config_loaded:
    app.logger.warning("Default config was loaded. "
                       "Change FLASK_CONFIG value to absolute path of your config file for correct loading.")

manager = LoginManager(app)  # Init login manager
csrf = CSRFProtect(app)  # Init CSRF in WTForms for excluding it in interaction with phone (well...)
url_tokenizer = URLSafeTimedSerializer(app.config['SECRET_KEY'])  # Serializer for generating email confirmation tokens
mail = Mail(app)  # For sending confirmation emails


def create_file(login, device_id, begin, end):
    """Generates file with data"""
    name = login + '_' + device_id.replace(':', '')
    query = "select * from {} where Clitime between '{}' and '{}'".format(name, begin, end)
    """ Код до мерджа с докером
    clientdb = Client(host='172.30.7.214', password = click_password)
    res = clientdb.execute(query)
    """
    res = get_clickhouse_data(query)
    file_name = name + '_' + str(random.randint(1, 1000000)) + '.csv'

    d = Device.select().where(Device.user.login==login)
    d_type = d.device_type

    device = d.device_type
    columns = device.columns.split(',')

    with open('files/' + file_name, 'w+') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(columns)
        for row in res:
            csv_out.writerow(row)

    return file_name


@manager.user_loader
def load_user(login):
    """Configure user loader"""
    return Operator.select().where(Operator.login==login)


@app.route('/auth/', methods=['POST'])
@csrf.exempt
def authenticate():
    data = request.json
    if data['login'] and data['password']:
        confirmed, jwt, code, login = auth.check_user(data['login'], data['password'])
        return jsonify({'jwt':jwt, "confirmed": confirmed, "login":login}), code
    return jsonify({}), 403


@app.route('/')
def main():
    """Index page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('get_data'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    """Login page"""
    form = LoginForm()
    if request.method == 'POST':
        operator = Operator.select().where(Operator.login==form.username.data)
        if operator and operator.password_valid(form.password.data):
            login_user(operator)
            return redirect(url_for('main'))
        form.validate_on_submit()
        if not operator:
            form.username.errors.append("Пользователь не зарегистрирован")
        elif not operator.password_valid(form.password.data):
            form.password.errors.append("Неверное имя или пароль")
    return render_template("login.html", form=form)


from blueprints.admins import bp as admins_bp
app.register_blueprint(blueprint=admins_bp, url_prefix='/admins')


@app.route('/data/', methods=["POST", "GET"])
@login_required
def get_data():
    if request.method == 'POST':
        form = UserList()
        login = form.us_list.data
        form2 = UserData()
        devices = []
        session["login"] = login

        for d in Device.select().where(Device.user.login == login):
            devices.append((d.device_id, d.device_name))

        form2.device.choices = devices
        return render_template('data2.html', form=form2)
    else:
        form = UserList()
        form.us_list.choices = [
            (u.login, "{} {} {}".format(u.name, u.surname, u.patronymic))
            for u in User.select()
            if current_user.id in u.allowed
        ]

        return render_template('data.html', form=form)


@app.route('/data/next/', methods=["POST", "GET"])
@login_required
def get_data_second():
    form = UserData()
    device = form.device.data
    app.logger.info(device)
    date_begin = form.date_begin.data
    date_end = form.date_end.data

    file = create_file(session['login'], device, date_begin, date_end)
    return render_template('upload_file.html', name=session['login'], file=file)


@app.route('/users/', methods=["POST", "GET"])
@login_required
def user_info():
    if request.method == 'GET':
        form = UserList()
        form.us_list.choices = [
            (u.login, "{} {} {}".format(u.name, u.surname, u.patronymic))
            for u in User.select()
            if current_user.id in u.allowed
        ]
        return render_template('user_info.html', form=form)
    else:
        form = UserList()
        d = {}
        q = User.select().where(User.login==form.us_list.data)
        for i in q:
            d[i] = q[i]
        return render_template('user_info_data.html', user=d)


@app.route('/download/<file>')
@login_required
def download_file(file):
    return send_file('files/' + file, as_attachment=True)


@app.route('/users/register/', methods=['POST'])
@csrf.exempt
def new_user():
    data = request.get_json()
    resp = User.select().where(User.email==data['email'])
    if resp:
        app.logger.info("User with provided email already exists")
    if User.select().where(User.login==data["login"]):
        return {"error": "login"}, 200

    token = encode_token(
        data,
        secret=settings.EMAIL_JWT_KEY, 
        iss=settings.SERVICE_NAME,
        exp=time() + settings.EMAIL_LINK_LIFETIME,
        iat=time()
    )
    msg = Message('Confirm Email', sender='iomt.confirmation@gmail.com', recipients=[data['email']])
    link = url_for('confirm_email', token=token, _external=True)
    msg.body = 'Your link is {}'.format(link)
    mail.send(msg)
    return {"error": ""}, 200


@app.route('/confirm_email/<token>')
def confirm_email(token):
    body = decode_token(token, secret=settings.EMAIL_JWT_KEY)
    body['password_hash'], body['salt'] = hash_password(body['password'])
    User.create(**body)
    return '<h1>Email confirmed!</h1>'

from blueprints.api import bp as api_bp
app.register_blueprint(api_bp)
csrf.exempt(api_bp)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='localhost')
