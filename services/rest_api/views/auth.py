from connexion import NoContent
from flask.views import MethodView
from flask import (
    abort,
    request,
)
import logging
from time import time
from datetime import datetime

from utils import encode_token
import settings
from models import (
    User,
    Operator,
)


class AuthView(MethodView):

    def post(self, user, token_info, body):
        expires = int(time()) + settings.JWT_TOKEN_LIFETIME
        # Такое форматирование чревато тем, 
        # что токены выпущенные для удаленного пользователя с id=n
        # будут валидны при переиспользовании id для нового поьзователя
        # по идее такого переиспользования не должно быть, но указать на это стоит
        if type(user) is User and 'user' in request.path:
            uri = f'user/{user.id}'
        elif type(user) is Operator:
            # Отсутствие тут проверки operator в path это огромный костыль для работы mosquitto
            uri = f'operator/{user.id}'
        else:
            abort(403)
        token = encode_token(
            sub=uri,
            iss=settings.SERVICE_NAME,
            exp=expires,
            iat=int(time()),
        )
            
        return {
            'token': token,
            'expires': datetime.fromtimestamp(expires).astimezone(),
        } 

    post_user = post_operator = post

    def get(self, user, token_info):
        return {
            'expires': datetime.fromtimestamp(token_info['exp']).astimezone()
        }
