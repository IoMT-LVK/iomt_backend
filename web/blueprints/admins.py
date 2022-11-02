import flask
from flask_login import login_required, current_user
from flask import current_app
from mongoengine import DoesNotExist

# noinspection PyUnresolvedReferences
import forms
# noinspection PyUnresolvedReferences
from models import Admins, Operators, Devices
# noinspection PyUnresolvedReferences
import models

bp = flask.Blueprint('admins', __name__)


@bp.route('/', methods=['GET'])
@login_required
def admin_panel():
    if not isinstance(current_user, models.Admins):
        flask.abort(404)
    current_app.logger.info(f"Admin ({current_user.login}) come on admin panel")
    ops = Operators.objects
    device_types = Devices.objects
    current_app.logger.debug(f"Devices: {device_types}")
    return flask.render_template("admin_panel.html", operators=ops, devices=device_types)


@bp.route('/add-operator/', methods=['GET', 'POST'])
@login_required
def admin_add_operator():
    form = forms.AddOperator()
    if not isinstance(current_user, models.Admins):
        flask.abort(404)
    if form.validate_on_submit():
        current_app.logger.info(f"Admin ({current_user.login}) created operator {form.login.data}")
        op = Admins() if form.is_admin.data else Operators()
        op.login = form.login.data
        op.password = form.password.data
        op.save()
        return flask.redirect(flask.url_for('admins.admin_panel'))

    return flask.render_template("add_operator.html", form=form)


@bp.route('/delete-operator/<string:login_for_del>', methods=['GET'])
@login_required
def admin_delete_operator(login_for_del):
    if not isinstance(current_user, models.Admins):
        flask.abort(404)
    current_app.logger.info(f"Admin ({current_user.login}) deleted user ...")
    try:
        ops = Operators.objects.get(login=login_for_del)  # TODO: same login problem
    except DoesNotExist:
        ops = Admins.objects.get_or_404(login=login_for_del)
    ops.delete()
    return flask.redirect(flask.url_for('admins.admin_panel'))


@bp.route('/add-device/', methods=['GET', 'POST'])
@login_required
def add_device_type():
    # TODO Implement
    return flask.redirect('admin_panel')


@bp.route('/delete-device/<string:id_for_del>/', methods=['GET'])
@login_required
def delete_device_type(id_for_del):
    # TODO: implement device deletion
    return flask.redirect(flask.url_for('admin_panel'))
