from flask import Flask, render_template, request, redirect, session, send_file, jsonify, url_for, send_from_directory

from forms import *
from blueprints.api import get_clickhouse_data
from flask_wtf.csrf import CSRFProtect
import models2
from werkzeug.security import generate_password_hash
from flask_login import current_user, login_user, login_required, logout_user, LoginManager
import auth
import random
import csv
import uuid
import os
import logging
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from utils import encode_token, decode_token, hash_password
import settings as settings
from time import time
import peewee
import traceback
import clickhouse_connect as clickhouse
import datetime

Operator, User, DeviceType, Device, db = models2.Operator, models2.User, models2.DeviceType, models2.Device, models2.db

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

API_USERNAME = "mqttUser"
API_PASSWORD = "resUttqm"

CH_HOST = 'clickhouse'
CH_USER = API_USERNAME
CH_PASSWORD = API_PASSWORD
CH_DATABASE = 'IoMT_DB'
CH_TABLENAME_FORMAT = '{user_id}_{slug}_{freq}'
CH_SESSIONS_FORMAT = 'sessions_{user_id}_{slug}_{freq}'


@app.before_request
def connect_db():
    db.connect(reuse_if_open=True)

@app.teardown_request
def db_disconnect(exc):
    if not db.is_closed():
        db.close()


def create_file(login, dev_name, start, end):
    """Generates file with data"""
    clh_client = clickhouse.get_client(
        host=CH_HOST,
        user=CH_USER,
        password=CH_PASSWORD,
        database=CH_DATABASE,
        client_name=CH_USER,
    )
    data = list()
    app.logger.info(f"Selecting data in range {start} to {end} from clickhouse")
    for freq in settings.FREQ:
        table_name = CH_TABLENAME_FORMAT.format(
            user_id=login,
            slug=dev_name,
            freq=freq
        )
        try:
            res = clh_client.query(f"""SELECT * FROM {table_name} WHERE timestamp >= '{start[::-1].replace(":", ".")[::-1]}' AND timestamp <= '{end[::-1].replace(":", ".")[::-1]}'""")
            data.extend(res.result_rows)
        except Exception as e:
            app.logger.error(traceback.format_exception(e))

    if not os.path.exists('files/'):
        os.mkdir('files')
    file_name = login + datetime.datetime.now().strftime('%d-%m-%Y_%H:%M:%S.%f') + ".csv"
    columns = ["Time", "Value"]
    with open(os.path.join('files/', file_name), 'w+') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(columns)
        for row in data:
            csv_out.writerow(row)

    return os.path.join('files/', file_name)


def get_allowed_users(op):
    users = User.select()
    result = list()
    app.logger.info(f"Operator {op.login} is {op.is_admin}")
    for u in users:
        app.logger.info(u.login)
        if op.is_admin:
            result.append(u)
            continue
        for x in u.allowed:
            if x.login == op.login:
                result.append(u)
                break
    return result


@manager.user_loader
def load_user(login):
    """Configure user loader"""
    res = None
    query = Operator.select().where(Operator.login==login)
    for x in query:
        res = x
    app.logger.warning(f"Searching for {res}")
    return res


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
        app.logger.warning(f"================= {Operator} ==================")
        app.logger.warning(f"================= {peewee.Metadata(Operator).table} ==================")
        try:
            operator = Operator.select().where(Operator.login==form.username.data)[0]
        except Exception as e:
            app.logger.error(f"No operator {form.username.data}")
            app.logger.error(traceback.format_exception(e))
            return render_template("login.html", form=form)

        app.logger.warning(f"================= {operator} ==================")
        app.logger.warning(f"{operator.password_hash} ---- {form.password.data} ---- {type(operator)}")
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
        allowed = get_allowed_users(current_user)
        form.us_list.choices = [
            (u.login, "{} {} {}".format(u.name, u.surname, u.patronymic))
            for u in allowed
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
            (u.login, "{}: {} {}".format(u.login, u.name, u.surname))
            for u in User.select()
            if current_user.id in u.allowed or current_user.is_admin
        ]
        return render_template('user_info.html', form=form)
    else:
        form = UserList()
        q = User.select().where(User.login==form.us_list.data)
        for i in q:
            d = i
        return render_template('user_info_data.html', user=d)


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


@app.route('/<login>/sessions', methods=['GET', 'POST'])
@csrf.exempt
def get_sessions(login):
    """Interface for operator to see users sessions"""
    app.logger.info(list((u.login for u in get_allowed_users(current_user))))
    if login not in list((u.login for u in get_allowed_users(current_user))):
        return redirect(url_for('main'))
    clh_client = clickhouse.get_client(
        host=CH_HOST,
        user=CH_USER,
        password=CH_PASSWORD,
        database=CH_DATABASE,
        client_name=CH_USER,
    )
    # create table karlstedt20148/fsdfsd/99:55/50;
    devices = Device.select().where(Device.user==User.select().where(User.login==login))
    all_sessions = list()
    for dev in devices:
        for freq in settings.FREQ:
            table = CH_SESSIONS_FORMAT.format(
                user_id=login,
                mac=dev.mac,
                slug=dev.device_type.name,
                freq=freq
            )
            app.logger.info(f"Selecting data from {table}")
            try:
                sessions_data = clh_client.query(f"""SELECT * FROM {table}""")
                all_sessions.extend(sessions_data.result_rows)
            except Exception as e:
                app.logger.error(traceback.format_exception(e))
    return render_template('list_sessions.html', sessions=all_sessions)


@app.route('/<login>/devices', methods=['GET'])
@csrf.exempt
def get_devices(login):
    """Interface for operator to see users sessions"""
    if login not in list((u.login for u in get_allowed_users(current_user))):
        return redirect(url_for('main'))
    devices = Device.select().where(Device.user==User.select().where(User.login==login))
    return render_template('list_devices.html', devices=devices)


@app.route('/select', methods=['GET', 'POST'])
@csrf.exempt
def select_data():
    """Interface for operator to select needed data from a particular user"""
    form = GetData()
    if form.validate_on_submit():
        login = form.user_login.data
        if login not in list((u.login for u in get_allowed_users(current_user))):
            return redirect(url_for('main'))
        return redirect(url_for('graphic', login=form.user_login.data, dev_name=form.device_name.data,
                                mac=form.mac.data, start=form.start_date.data.strftime('%Y-%m-%d %H:%M:%S:%f'),
                                end=form.end_date.data.strftime('%Y-%m-%d %H:%M:%S:%f')))
    return render_template('select_data.html', form=form)


@app.route('/download', methods=['GET', 'POST'])
@csrf.exempt
def download_data():
    """Interface for operator to download needed data from a particular user"""
    form = GetData()
    if form.validate_on_submit():
        login = form.user_login.data
        if login not in list((u.login for u in get_allowed_users(current_user))):
            return redirect(url_for('main'))
        filename = create_file(login=form.user_login.data, dev_name=form.device_name.data,
                               start=form.start_date.data.strftime('%Y-%m-%d %H:%M:%S:%f'),
                                end=form.end_date.data.strftime('%Y-%m-%d %H:%M:%S:%f'))
        return send_file(filename)
    return render_template('select_data.html', form=form)


@app.route('/select/result', methods=['GET', 'POST'])
@csrf.exempt
def graphic():
    try:
        login, dev_name, mac, start, end = request.args["login"], request.args["dev_name"], request.args["mac"], request.args["start"], request.args["end"]
    except Exception as e:
        app.logger.error(traceback.format_exception(e))
        return
        
    if login not in list((u.login for u in get_allowed_users(current_user))):
        app.logger.error(f"No access for operator {current_user.login} to user {login}")
        return redirect(url_for('main'))
    clh_client = clickhouse.get_client(
        host=CH_HOST,
        user=CH_USER,
        password=CH_PASSWORD,
        database=CH_DATABASE,
        client_name=CH_USER,
    )
    data = list()
    app.logger.info(f"Selecting data in range {start} to {end} from clickhouse")
    for freq in settings.FREQ:
        table_name = CH_TABLENAME_FORMAT.format(
            user_id=login,
            slug=dev_name,
            freq=freq
        )
        try:
            res = clh_client.query(f"""SELECT * FROM {table_name} WHERE timestamp >= '{start[::-1].replace(":", ".")[::-1]}' AND timestamp <= '{end[::-1].replace(":", ".")[::-1]}'""")
            data.extend(res.result_rows)
        except Exception as e:
            app.logger.error(traceback.format_exception(e))
    return render_template('display_data.html', data=data)


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
