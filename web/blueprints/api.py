import flask
from flask import current_app
from clickhouse_driver import Client

import forms  # noqa
import models  # noqa
import auth  # noqa


bp = flask.Blueprint('api', __name__)


def get_clickhouse_data(query):
    clickhouse_client = Client(host=current_app.config['CLICKHOUSE_HOST'],
                               password=current_app.config['CLICKHOUSE_PASS'])  # ClickHouse config
    return clickhouse_client.execute(query)


@bp.route('/users/info/', methods=['GET', 'POST'])
def get_info():
    token = flask.request.args.get('token')
    user_id = flask.request.args.get('user_id')
    if not token or not user_id or not auth.check_token(token):
        return {}, 403
    if flask.request.method == 'GET':
        info = models.Info.objects(user_id=user_id).first()
        weight = 0 if not info.weight else info.weight
        height = 0 if not info.height else info.height
        return {"weight": weight, "height": height, "name": info.name, "surname": info.surname,
                "patronymic": info.patronymic, "email": info.email, "birthdate": info.birth_date,
                "phone_number": info.phone}, 200
    else:
        data = flask.request.get_json()
        info = models.Info.objects(user_id=user_id).first()
        info.weight = data['weight']
        info.height = data['height']
        info.email = data['email']
        info.name = data['name']
        info.surname = data['surname']
        info.patronymic = data['patronymic']
        info.birth_date = data['birthdate']
        info.phone = data['phone_number']
        info.save()
        return {}, 200


@bp.route('/users/allow/', methods=["POST"])
def allow_operator():
    """Allow access for concrete operator"""
    token = flask.request.args.get('token')
    user_id = flask.request.args.get('user_id')
    op_id = flask.request.args.get('operator_id')
    if not token or not user_id or not auth.check_token(token):
        return {}, 403
    op = models.Operators.objects.get_or_404(id=op_id)
    models.Info.objects(user_id=user_id).update_one(add_to_set__allowed=op.id)
    return {}, 200


@bp.route('/devices/register/', methods=['POST'])
def register_device():
    token = flask.request.args.get('token')
    # FIXME: Дыра, любой зареганый пользователь может зарегать на другого девайс
    user_id = flask.request.args.get('user_id')
    if not token or not user_id or not auth.check_token(token):
        return {}, 403
    data = flask.request.get_json()
    device = models.Userdevices()
    device.user_id = user_id
    device.device_id = data['device_id']
    device.device_name = data['device_name']
    device.device_type = data['device_type']
    device.save()

    table_name = user_id + '_' + data['device_id'].replace(':', '')
    current_app.logger.info("TABLE %s", table_name)
    obj = models.Devices.objects(device_type=data['device_type']).first()
    if not obj:
        return {}, 403

    create_str = obj.create_str.format(table_name)
    current_app.logger.info("CREATE %s", create_str)

    clickhouse_client.execute(create_str)
    return {}, 200


@bp.route('/devices/get/', methods=['GET'])
def get_user_devices():
    token = flask.request.args.get('token')
    user_id = flask.request.args.get('user_id')
    if not token or not user_id or not auth.check_token(token):
        return {}, 403
    objects = models.Userdevices.objects(user_id=user_id)
    user_devices = [
        {"device_id": obj.device_id, "device_name": obj.device_name, "device_type": obj.device_type}
        for obj in objects
    ]
    return flask.jsonify({"devices": user_devices}), 200


@bp.route('/devices/types/', methods=['GET'])
def get_devices():
    token = flask.request.args.get('token')
    type_id = flask.request.args.get('id')
    if not token or not auth.check_token(token):
        return {'message': "invalid token", "token": token}, 403
    with open(f"device_type_cfgs/{type_id}.toml", 'rt') as f:
        return f.read()
    # return flask.send_from_directory('device_type_cfgs', f"{type_id}.toml") if type_id == '1' else flask.abort(404, f"Config_id {type_id} not found")  # FIXME
    if type_id is str and type_id.isdecimal():
        models.Devices.objects()
    models.Devices.objects(id=type_id).first()
    devices_types = [
        {"device_type": obj.device_type, "prefix": obj.prefix}
        for obj in models.Devices.objects()
    ]
    for obj in models.Devices.objects():
        devices_types.append({"device_type": obj.device_type, "prefix": obj.prefix})
    return flask.jsonify({"devices": devices_types}), 200


@bp.route('/devices/delete/', methods=['GET'])
def delete_device():
    token = flask.request.args.get('token')
    user_id = flask.request.args.get('user_id')
    device_id = flask.request.args.get('id')
    if not token or not user_id or not auth.check_token(token):
        return {}, 403
    d = models.Userdevices.objects(user_id=user_id, device_id=device_id).first()
    d.delete()
    return {}, 200


@bp.route('/jwt/', methods=['GET'])
def jwt():
    token = flask.request.args.get('token')
    if not token or not auth.check_token(token):
        return flask.jsonify({"valid": False})
    else:
        return flask.jsonify({"valid": True})
