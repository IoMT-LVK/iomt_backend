from flask import Flask, render_template, request, redirect, session, send_file, jsonify, url_for

from forms import *
from blueprints.api import get_clickhouse_data
from flask_wtf.csrf import CSRFProtect
from models import db, Users, Operators, Devices, Userdevices, Info
from werkzeug.security import generate_password_hash
from flask_login import current_user, login_user, login_required, logout_user, LoginManager
import auth
import random
import csv
import uuid
import logging
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired


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

db.init_app(app)  # Init mongoengine
manager = LoginManager(app)  # Init login manager
csrf = CSRFProtect(app)  # Init CSRF in WTForms for excluding it in interaction with phone (well...)
url_tokenizer = URLSafeTimedSerializer(app.config['SECRET_KEY'])  # Serializer for generating email confirmation tokens
mail = Mail(app)  # For sending confirmation emails


def create_file(user_id, device_id, begin, end):
    """Generates file with data"""
    name = user_id + '_' + device_id.replace(':', '')
    query = "select * from {} where Clitime between '{}' and '{}'".format(name, begin, end)
    """ Код до мерджа с докером
    clientdb = Client(host='172.30.7.214', password = click_password)
    res = clientdb.execute(query)
    """
    res = get_clickhouse_data(query)
    file_name = name + '_' + str(random.randint(1, 1000000)) + '.csv'

    d = Userdevices.objects(user_id=user_id).first()
    d_type = d.device_type

    device = Devices.objects(device_type=d_type).first()
    columns = device.columns.split(',')

    with open('files/' + file_name, 'w+') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(columns)
        for row in res:
            csv_out.writerow(row)

    return file_name


@manager.user_loader
def load_user(user_id):
    """Configure user loader"""
    return Operators.objects(pk=user_id).first()


@app.route('/auth/', methods=['POST'])
@csrf.exempt
def authenticate():
    data = request.json
    if data['login'] and data['password']:
        confirmed, jwt, code, user_id = auth.check_user(data['login'], data['password'])
        return jsonify({'jwt':jwt, "confirmed": confirmed, "user_id":user_id}), code
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
        operator = Operators.objects(login=form.username.data).first()
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
        user_id = form.us_list.data
        form2 = UserData()
        devices = []
        session["user_id"] = user_id

        for d in Userdevices.objects(user_id=user_id):
            devices.append((d.device_id, d.device_name))

        form2.device.choices = devices
        return render_template('data2.html', form=form2)
    else:
        form = UserList()
        form.us_list.choices = [
            (u.user_id, "{} {} {}".format(u.name, u.surname, u.patronymic))
            for u in Info.objects
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

    file = create_file(session['user_id'], device, date_begin, date_end)
    return render_template('upload_file.html', name=session['user_id'], file=file)


@app.route('/users/', methods=["POST", "GET"])
@login_required
def user_info():
    if request.method == 'GET':
        form = UserList()
        form.us_list.choices = [
            (u.user_id, "{} {} {}".format(u.name, u.surname, u.patronymic))
            for u in Info.objects
            if current_user.id in u.allowed
        ]
        return render_template('user_info.html', form=form)
    else:
        form = UserList()
        d = {}
        q = Info.objects(user_id=form.us_list.data).first()
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
    man_info = Info.objects(email=data['email']).first()
    if man_info:
        man_user = Users.objects(user_id=man_info.user_id).first()
        if man_user.confirmed:
            return {"error": "email"}, 200
        else:
            man_info.delete()
            man_user.delete()
    if Users.objects(login=data['login']).first():
        return {"error": "login"}, 200
    id = uuid.uuid4().hex
    usr = Users()
    usr.user_id = id
    usr.login = data['login']
    usr.password_hash = generate_password_hash(data['password'])
    usr.confirmed = False
    usr.save()

    info = Info()
    info.user_id = id
    info.email = data['email']
    info.name = data['name']
    info.surname = data['surname']
    info.patronymic = data['patronymic']
    info.birth_date = data['birthdate']
    info.phone = data['phone_number']
    info.weight = 0
    info.height = 0
    info.save()

    token = url_tokenizer.dumps(data['email'], salt='email-confirm')
    msg = Message('Confirm Email', sender='iomt.confirmation@gmail.com', recipients=[data['email']])
    link = url_for('confirm_email', user_id=id, token=token, _external=True)
    msg.body = 'Your link is {}'.format(link)
    mail.send(msg)
    return {"error": ""}, 200


@app.route('/confirm_email/<user_id>/<token>')
def confirm_email(user_id, token):
    try:
        url_tokenizer.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        return '<h1>The link is expired!</h1>'
    user = Users.objects(user_id=user_id).first()
    user.confirmed = True
    user.save()
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
