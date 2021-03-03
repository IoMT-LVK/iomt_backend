import os
from flask import Flask, render_template, request, redirect, session
from forms import *
from flask_wtf.csrf import CSRFProtect
from models import db, Users, Operators
from werkzeug.security import generate_password_hash, check_password_hash

#HeartRate, RespRate, Insp, Exp, Steps, Activity, Cadence
params = [("HeartRate", "Частота сердцебиения"), ("RespRate", "Частота дыхания"),
          ("Insp", "Вдох"), ("Exp", "Выдох"), ("Steps", "Число шагов"), ("Activity", "Интенсиовность активности"),
          ("Cadence", "Каденция")]

app = Flask(__name__)
csrf = CSRFProtect(app)

SECRET_KEY = os.urandom(43)
app.config['SECRET_KEY'] = SECRET_KEY

db.init_app(app)

@app.route('/')
def main():
    if (not session.get('operator')):
        return redirect('/login/')
    else:
        return redirect('/data/')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        operator = Operators.objects(login=form.username.data).first()
        if operator and operator.password_valid(form.password.data):
            session["operator"] = form.username.data
            return redirect("/")
        else:
            if (not operator):
                tmp = form.username.errors
                tmp = list(tmp)
                tmp.append("Логин не зарегистрирован")
                form.username.errors = tmp
            elif not operator.password_valid(form.password.data):
                tmp = form.password.errors
                tmp = list(tmp)
                tmp.append("Неверное имя или пароль")
                form.password.errors = tmp

    return render_template("login.html", form=form)


@app.route('/data/', methods=["POST", "GET"])
def get_data():
    if (not session.get('operator')):
        return redirect('/')
    if request.method == 'POST':
        form = UserList()
        user = form.us_list.data
        session["user_data"] = user
        #TO DO
        form2 = UserData()
        form2.params = params
        return render_template('data2.html', form=form2)
    else:
        form = UserList()
        user_list = []
        for u in Users.objects:
            user_list.append((u.user_id, "{} {} {}".format(u.surname, u.name, u.patronymic)))
        form.us_list.choices = user_list
        return render_template('data.html', form=form)


@app.route('/data2/', methods=["POST", "GET"])
def get_data_second():
    if (not session.get('operator')):
        return redirect('/')
    form = UserData()
    if form.validate_on_submit():
        date_begin = form.date_begin.data
        date_end = form.date_end.data
        #params = form.params.data
        #TO DO
        return render_template('upload_file.html', name=session['user_data'])
    else:
        return render_template('data2.html', form=form)


@app.route('/adduser/', methods=["POST", "GET"] )
def add_user():
    if (not session.get('operator')):
        return redirect('/')
    if request.method == 'POST':
        form = AddUser()

        usr = Users()
        usr.user_id = len(Users.objects) + 1
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
        print(form.email.data)
        print(usr.email)
        usr.save()

        return render_template('add_success.html', name=form.name.data, surname=form.surname.data)
    else:
        form = AddUser()
        return render_template('add_user.html', form=form)

@app.route('/users/', methods=["POST", "GET"] )
def user_info():
    if (not session.get('operator')):
        return redirect('/')
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


@app.route('/logout/')
def logout():
    del session['operator']
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
