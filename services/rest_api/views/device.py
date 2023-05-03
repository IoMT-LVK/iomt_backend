import re
from connexion import NoContent
from flask.views import MethodView
from flask import abort

from models import (
    User,
    Operator,
)


class DeviceView(MethodView):

    def _check_account_type(self, user):
        if type(user) is not User:
            abort(403)
    
    def _check_permission(self, user, body={}, id=None):
        # Пока поле user_id всегда должно равняться id запрашивающего
        # Но в перспективе закладываем возможность регистрации девайса от оператора
        if body.get('user_id') and body.get('user_id') != user.id:
            abort(403)
        if id is not None and Device.get_or_none(Device.id == id).user == user:
            abort(403)

    def post(self, user, token_info, body):
        self._check_account_type(user)
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

    def put(self, user, token_info):
        print(self.put.__qualname__)
        return NoContent

    def delete(self, user, token_info):
        print(self.delete.__qualname__)
        return NoContent

    def get(self, user, token_info, id=None):
        self._check_account_type(user)
        self._check_permission(user, id=id)
        if id is None:
            id = user.id

        return 


__all__ = [
    "DeviceView",
]
