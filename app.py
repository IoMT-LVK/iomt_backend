import os
from flask import Flask, render_template, request, redirect, session, send_file
from forms import *
from flask_wtf.csrf import CSRFProtect
from models import db, Users, Operators, Devices, Registerdevices
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_user, login_required, logout_user, LoginManager
import auth
import uuid

import logging

#HeartRate, RespRate, Insp, Exp, Steps, Activity, Cadence
params = [("HeartRate", "Частота сердцебиения"), ("RespRate", "Частота дыхания"),
          ("Insp", "Вдох"), ("Exp", "Выдох"), ("Steps", "Число шагов"), ("Activity", "Интенсиовность активности"),
          ("Cadence", "Каденция")]

app = Flask(__name__)
csrf = CSRFProtect(app)
manager = LoginManager(app)

SECRET_KEY = os.urandom(43)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MONGODB_SETTINGS'] = {
    'db': 'data',
    'host': 'localhost'
}
app.config['WTF_CSRF_CHECK_DEFAULT'] = False
app.config['SESSION_COOKIE_SECURE'] = False

db.init_app(app)
manager.init_app(app)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)

@manager.user_loader
def load_user(user_id):
    return Operators.objects(pk=user_id).first()

@app.route('/auth/')
def auth():
    data = request.get_json()
    if data['username'] and data['password']:
        jwt, code = auth.check_user(data['username'], data['password'])
        return {'jwt':jwt}, code
    return {}, 403

@app.route('/')
def main():
    if not current_user.is_authenticated:
        return redirect('http://iomt.lvk.cs.msu.su/login/')
    else:
        app.logger.info("HERE")
        return redirect('http://iomt.lvk.cs.msu.su/data/')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        app.logger.info('data %s %s', form.username.data, form.password.data)
        operator = Operators.objects(login=form.username.data).first()
        if operator and operator.password_valid(form.password.data):
            app.logger.info('Success!')
            login_user(operator)
            app.logger.info('auth %s', current_user.is_authenticated)
            return redirect("http://iomt.lvk.cs.msu.su/")
        else:
            tmp = form.username.errors
            tmp = list(tmp)
            if not operator:
                tmp.append("Пользователь не зарегистрирован")
                form.username.errors = tmp
            elif not operator.password_valid(form.password.data):
                tmp.append("Неверное имя или пароль")
                form.password.errors = tmp
    return render_template("login.html", form=form)


@app.route('/data/', methods=["POST", "GET"])
@login_required
def get_data():
    if request.method == 'POST':
        form = UserList()
        user = form.us_list.data
        #TODO
        form2 = UserData()
        devices = []
        login = Users.objects(user_id=user).first().login
        session["user_data"] = login

        for d in Registerdevices.objects(user=login):
            print(login, (d.device_id, d.device))
            devices.append((d.device_id, d.device))

        form2.device.choices = devices
        return render_template('data2.html', form=form2)
    else:
        form = UserList()
        user_list = []
        for u in Users.objects:
            user_list.append((u.user_id, "{} {} {}".format(u.surname, u.name, u.patronymic)))
        form.us_list.choices = user_list
        return render_template('data.html', form=form)


@app.route('/data2/', methods=["POST", "GET"])
@login_required
def get_data_second():
    form = UserData()
    device = form.device.data
    date_begin = form.date_begin.data
    date_end = form.date_end.data
    # params = form.params.data
    # TODO
    return render_template('upload_file.html', name=session['user_data'])



@app.route('/adduser/', methods=["POST", "GET"] )
@login_required
def add_user():
    if request.method == 'POST':
        form = AddUser()
        usr = Users()
        usr.user_id = uuid.uuid4().hex
        usr.name = form.name.data
        usr.password_hash = generate_password_hash(form.password.data)
        usr.surname = form.surname.data
        usr.login = form.login.data
        usr.patronymic = form.patronymic.data
        usr.birth_date = form.age.data
        usr.weight = form.weight.data
        usr.height = form.height.data
        usr.phone_number = form.phone_number.data
        usr.email = form.email.data
        usr.save()

        return render_template('add_success.html', name=form.name.data, surname=form.surname.data)
    else:
        form = AddUser()
        return render_template('add_user.html', form=form)



@app.route('/users/', methods=["POST", "GET"] )
@login_required
def user_info():
    if request.method == 'GET':
        form = UserList()
        user_list = []
        for u in Users.objects:
            user_list.append((u.user_id, "{} {} {}".format(u.surname, u.name, u.patronymic)))
        form.us_list.choices = user_list
        return render_template('user_info.html', form=form)
    else:
        form = UserList()
        d = {}
        q = Users.objects(user_id=form.us_list.data).first()
        for i in q:
            d[i] = q[i]
        return render_template('user_info_data.html', user=d)

@app.route('/devices/', methods=["POST", "GET"] )
@login_required
def devices():
    objects = Devices.objects()
    devices = {}
    for item in objects:
        if not item.device in devices:
            devices[item.device] = []
        devices[item.device].append([item.sensor, item.sensor_name])
    return render_template('devices.html', devices=devices)


@app.route('/devices/add/', methods=["POST", "GET"] )
@login_required
def add_device():
    if request.method == 'GET':
        form = AddDevice()
        return render_template('add_device.html', form=form)
    else:
        form = AddDevice()
        srs = form.sensors.data.split('\n')
        for it in srs:
            dvs = Devices()
            dvs.device = form.name.data
            it = it.split(' ')
            dvs.sensor = it[0]
            dvs.sensor_name = it[1]
            dvs.save()
        return redirect('/devices/')


@app.route('/download/')
@login_required
def download_file():
    path = 'file.txt'
    return send_file(path, as_attachment=True)

@app.route('/registering/', methods=['POST'])
@login_required
def new_user():
    data = request.json
    usr = Users()
    usr.user_id = uuid.uuid4().hex
    usr.name = data['name']
    usr.password_hash = data['password']
    usr.surname = data['surname']
    usr.login = data['login']
    usr.patronymic = data['patronymic']
    usr.birth_date = data['birthdate']
    usr.weight = data['weight']
    usr.height = data['height']
    usr.phone_number = data['phone_number']
    usr.email = data['email']
    usr.save()
    return 200


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
