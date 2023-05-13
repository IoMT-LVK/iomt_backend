import re
from connexion import NoContent
from flask import abort
from playhouse.flask_utils import get_object_or_404

from models import (
    Device,
    DeviceType,
    User,
)
from .base import BaseView


class DeviceView(BaseView):

    def _check_permission(self, user, body={}, device=None):
        # Пока поле user_id всегда должно равняться id запрашивающего
        # Но в перспективе закладываем возможность регистрации девайса от оператора
        if 'user_id' in body and body['user_id'] != user.id:
            abort(403)
        if device is not None and device.user != user:
            abort(403)

    def post(self, user, token_info, body):
        self._check_account_type(user, allow_user=True)
        self._check_permission(user, body)

        device_type = DeviceType.get_or_none(body['device_type_id'])
        if device_type is None:
            abort(400, "Unknown device type")

        device = Device.create(
            user=user, 
            device_type=device_type,
            mac=body['mac'],
        )

        return {'id': device.id} 

    def put(self, user, token_info, body, id):
        self._check_account_type(user, allow_user=True)
        device = get_object_or_404(Device, (Device.id == id))
        self._check_permission(user, body=body, device=device)
        Device.set_by_id(id, body)
        return NoContent

    def delete(self, user, token_info, id):
        self._check_account_type(user, allow_user=True)
        device = get_object_or_404(Device, (Device.id == id))
        self._check_permission(user, device=device)
        device.delete_instance()
        return NoContent

    def get(self, user, token_info, id=None):
        self._check_account_type(user, allow_user=True)
        device = get_object_or_404(Device, (Device.id == id))
        self._check_permission(user, device=device)
        return device.serialize()

class DevicesView(BaseView):

    def get(self, user, token_info):
        self._check_account_type(user, allow_user=True)
        users_devices = Device.select().where(Device.user == user).execute()
        return [device.serialize() for device in users_devices]


__all__ = [
    "DeviceView",
    "DevicesView",
]
