from flask.views import MethodView
from flask import abort


class BaseView(MethodView):

    def _check_account_type(
        self, 
        allow_user=False,
        allow_operator=False,
        allow_admin=False,
    ):
        if (
            allow_user and type(user) is User or
            allow_operator and type(user) is Operator or
            allow_admin and type(user) is Opertor and user.is_admin
        ):
            return
        abort(403)
    
    def post(self, user, token_info, body):
        raise NotImplementedError

    def put(self, user, token_info):
        raise NotImplementedError

    def delete(self, user, token_info):
        raise NotImplementedError

    def get(self, user, token_info, id=None):
        raise NotImplementedError


__all__ = [
    "BaseView",
]
