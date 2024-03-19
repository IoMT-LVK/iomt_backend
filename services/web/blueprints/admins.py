import flask
from flask_login import login_required, current_user
from flask import current_app
from utils import hash_password
from wtforms import StringField, SubmitField, IntegerField, FloatField, SelectField, SelectMultipleField, PasswordField, \
    TextAreaField, BooleanField
from wtforms.validators import DataRequired

# noinspection PyUnresolvedReferences
import forms
# noinspection PyUnresolvedReferences
from models2 import Operator, User, Device, DeviceType, Characteristic
# noinspection PyUnresolvedReferences

bp = flask.Blueprint('admins', __name__)


@bp.route('/', methods=['GET'])
@login_required
def admin_panel():
    if not current_user.is_admin:
        current_app.logger.info(f"Attempt to enter admin panel by {current_user.login}")
        flask.abort(404)
    current_app.logger.info(f"Admin ({current_user.login}) come on admin panel")
    ops = Operator.select()
    device_types = DeviceType.select()
    users = User.select()
    chars = Characteristic.select()
    current_app.logger.debug(f"Devices: {device_types}")
    return flask.render_template("admin_panel.html", operators=ops, devices=device_types, users=users, chars=chars)


@bp.route('/add-operator/', methods=['GET', 'POST'])
@login_required
def admin_add_operator():
    form = forms.AddOperator()
    if not current_user.is_admin:
        flask.abort(404)
    if form.validate_on_submit():
        current_app.logger.info(f"Admin ({current_user.login}) created operator {form.login.data}")
        passw_hash, salt = hash_password(form.password.data)
        Operator.create(login=form.login.data, password_hash=passw_hash, salt=salt, is_admin=(True if form.is_admin.data else False))
        return flask.redirect(flask.url_for('admins.admin_panel'))

    return flask.render_template("add_operator.html", form=form)


@bp.route('/delete-operator/<string:login_for_del>', methods=['GET'])
@login_required
def admin_delete_operator(login_for_del):
    if not current_user.is_admin:
        flask.abort(404)
    current_app.logger.info(f"Admin ({current_user.login}) deleted user ...")
    try:
        ops = Operator.get(Operator.login==login_for_del)  # TODO: same login problem
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
    form.chars.choices = [(c.slug, c.name) for c in Characteristic.select()]
    if form.validate_on_submit():
        device = DeviceType.create(name=form.name.data, type=form.tp.data)
        char_list = form.chars.data
        current_app.logger.info(", ".join(char_list))
        for x in char_list:
            ch = Characteristic.select().where(Characteristic.slug==x)
            device.characteristics.add(ch)
        return flask.redirect(flask.url_for('admins.admin_panel'))
    return flask.render_template("add_device.html", form=form)


@bp.route('/add-characteristic/', methods=['GET', 'POST'])
@login_required
def add_characteristic():
    form = forms.AddCharacteristic()
    if not current_user.is_admin:
        flask.abort(404)
    if form.validate_on_submit():
        Characteristic.create(name=form.name.data, slug=form.slug.data, service_uuid=form.sid.data, characteristic_uuid=form.cid.data)
        return flask.redirect(flask.url_for('admins.admin_panel'))
    return flask.render_template("add_characteristic.html", form=form)


@bp.route('/delete-device/<string:id_for_del>/', methods=['GET'])
@login_required
def delete_device_type(id_for_del):
    if not current_user.is_admin:
        flask.abort(404)
    # TODO: implement device deletion
    return flask.redirect(flask.url_for('admins.admin_panel'))


@bp.route('/add-user/', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    form = forms.AddUser()
    if not current_user.is_admin:
        flask.abort(404)
    if form.validate_on_submit():
        current_app.logger.info(f"Admin ({current_user.login}) created user {form.login.data}")
        passw_hash, salt = hash_password(form.password.data)
        User.create(login=form.login.data, password_hash=passw_hash, salt=salt, weight=form.weight.data, height=form.height.data, email=form.email.data, name=form.name.data,
                    surname=form.surname.data, patronymic=form.patronymic.data)
        return flask.redirect(flask.url_for('admins.admin_panel'))

    return flask.render_template("add_user.html", form=form)