from connexion import NoContent
from flask.views import MethodView
from flask import abort
from playhouse.flask_utils import get_object_or_404

from models import Operator
from utils import (
    hash_password,
)

class OperatorView(MethodView):

    # TODO: в connexion есть интересная фича decorators
    # она накидывает на все методы перечисленные декораторы
    # возможно будет удобно для определения запросов без id

    def post(self, user, token_info, body):
        if type(user) is not Operator or not user.is_admin:
            abort(403)
        body['password_hash'], body['salt'] = hash_password(body.pop('password'))
        op, created = Operator.get_or_create(
            login=body['login'],
            defaults=body,
        )
        if not created:
            abort(409)

        return {'id': op.id}, 201

    def put(self, user, token_info, body, id=None):
        if id == None:
            if type(user) is not Operator:
                abort(400)
            op, id = user, user.id
        else:
            op = get_object_or_404(Operator, (Operator.id == id))

        if (
            type(user) is Operator and
            (id == user.id or user.is_admin)
        ):
            if (
                'login' in body and
                Operator.get_or_none(Operator.login == body['login'])
            ):
                abort(409)

            if 'is_admin' in body and not user.is_admin:
                abort(403)

            if 'password' in body:
                body['password_hash'], body['salt'] = hash_password(body.pop('password'))

            Operator.set_by_id(op.id, body)
            return NoContent
        abort(403)

    def delete(self, user, token_info, id=None):
        if id is None:
            if type(user) is not Operator:
                abort(400)
            op, id = user, user.id
        else:
            op = get_object_or_404(Operator, (Operator.id == id))

        if (
            type(user) is Operator and
            (id == user.id or user.is_admin)
        ):
            op.delete_instance()
            return NoContent
        abort(403)

    def get(self, user, token_info, id=None):
        """Информация об операторах доступна всем пользователям и всем операторам"""
        if id is None:
            if type(user) is not Operator:
                abort(400)
            id = user.id

        op = get_object_or_404(Operator, (Operator.id == id))
        return op.serialize()
