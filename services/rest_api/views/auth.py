from connexion import NoContent
from flask.views import MethodView
from time import time
from datetime import datetime

from utils import encode_token
import dev_settings as settings
from models import (
    User,
    Operator,
)

class AuthView(MethodView):

    def post(self, user, token_info, body):
        expires = int(time()) + settings.JWT_TOKEN_LIFETIME
        if type(user) is User:
            uri = f'user/{user.id}'
        elif type(user) is Operator:
            uri = f'operator/{user.id}'
        else:
            raise ValueError()
        token = encode_token(
            sub=uri,
            iss=settings.SERVICE_NAME,
            exp=expires,
            iat=int(time()),
        )
            
        return {
            'token': token,
            'expires': datetime.fromtimestamp(expires),
        } 

    post_user = post_operator = post

    def get(self, user, token_info):
        return {
            'expires': datetime.fromtimestamp(int(token_info['exp'])),
        }
