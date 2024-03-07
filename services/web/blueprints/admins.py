import flask
from flask_login import login_required, current_user
from flask import current_app
from services.rest_api.utils import hash_password
from wtforms import StringField, SubmitField, IntegerField, FloatField, SelectField, SelectMultipleField, PasswordField, \
    TextAreaField, BooleanField
from wtforms.validators import DataRequired

# noinspection PyUnresolvedReferences
import forms
# noinspection PyUnresolvedReferences
from models2 import Operator, Device, DeviceType, Characteristic
# noinspection PyUnresolvedReferences
import models

bp = flask.Blueprint('admins', __name__)


@bp.route('/', methods=['GET'])
@login_required
def admin_panel():
    if not current_user.is_admin:
        current_app.logger.info(f"Attempt to enter admin panel by {current_user.login}")
        flask.abort(404)
    current_app.logger.info(f"Admin ({current_user.login}) come on admin panel")
    ops = Operator.select()
    device_types = Device.select()
    current_app.logger.debug(f"Devices: {device_types}")
    return flask.render_template("admin_panel.html", operators=ops, devices=device_types)


@bp.route('/add-operator/', methods=['GET', 'POST'])
@login_required
def admin_add_operator():
    form = forms.AddOperator()
    if not current_user.is_admin:
        flask.abort(404)
    if form.validate_on_submit():
        current_app.logger.info(f"Admin ({current_user.login}) created operator {form.login.data}")
        passw_hash, salt = hash_password(form.password.data)
        Operator.create(login=form.login.data, password=passw_hash, salt=salt, is_admin=(True if form.is_admin.data else False))
        return flask.redirect(flask.url_for('admins.admin_panel'))

    return flask.render_template("add_operator.html", form=form)


@bp.route('/delete-operator/<string:login_for_del>', methods=['GET'])
@login_required
def admin_delete_operator(login_for_del):
    if not current_user.is_admin:
        flask.abort(404)
    current_app.logger.info(f"Admin ({current_user.login}) deleted user ...")
    try:
        ops = Operator.select().get(Operator.login==login_for_del)  # TODO: same login problem
        current_app.logger.info(f"User {ops.login} is deleted")
        ops.delete_instance()
    except Exception:
        current_app.logger.info(f"Operator {login_for_del} does not exist")
    return flask.redirect(flask.url_for('admins.admin_panel'))


@bp.route('/add-device/', methods=['GET', 'POST'])
@login_required
def add_device_type():
    form = forms.AddDevice()
    if not current_user.is_admin:
        flask.abort(404)
    if flask.request.method == 'GET':
        return flask.render_template("add_device.html", form=form)
    if flask.request.form.get('add_char') is not None:
        form.__class__.amount += 1
        for i in range(form.__class__.amount):
            exec(f"form.ch_name_{i} = StringField('Имя характеристики', [DataRequired(message='Введите имя')])")
            exec(f"form.slug_{i} = StringField('slug', [DataRequired(message='Введите slug')])")
            exec(f"form.service_{i} = StringField('service', [DataRequired(message='Введите service')])")
            exec(f"form.char_uid_{i} = StringField('char_uid', [DataRequired(message='Введите char_uid')])")
        return flask.render_template("add_device.html", form=form)
    char_list = list()
    for x in range(form.__class__.amount):
        exec(f"slug, name, serv, char_uid = form.slug_{x}, form.ch_name_{x}, form.service_{x}, form.char_uid_{x}")
        char_list.append(Characteristic.create(name=name, slug=slug, service_uuid=serv, Characteristic_uuid=char_uid))
    device = DeviceType.create(name=form.name.data, type=form.tp.data)
    device.characteristics.add(char_list)
    form.__class__.amount = 0
    return flask.redirect('admin_panel')


@bp.route('/delete-device/<string:id_for_del>/', methods=['GET'])
@login_required
def delete_device_type(id_for_del):
    if not current_user.is_admin:
        flask.abort(404)
    # TODO: implement device deletion
    return flask.redirect(flask.url_for('admin_panel'))
