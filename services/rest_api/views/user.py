from connexion import NoContent
from connexion.exceptions import (
    Forbidden,
)
from flask.views import MethodView
from flask import abort
import logging
from smtplib import SMTPException
from time import time
from playhouse.flask_utils import get_object_or_404

from models import (
    User,
    Operator,
)
from exceptions import (
    CantSendEmailError,
)
from utils import (
    send_email,
    encode_token,
    decode_token,
    hash_password,
)

import dev_settings as settings

log = logging.getLogger(__name__)

class UserView(MethodView):

    def _send_reg_email(self, email, retpath, token):
        link = retpath + f"?token={token}"
        try:
            raise SMTPException
            send_email(
                subject="Commit registration on IoMT",
                text=f"Commit your registration on IoMT service, by clicking on link: {link}",
                to=email,
            )
        except SMTPException as e:
            log.error(f"Can't send email for {email} on retpath {retpath}, error: {str(e)}")
            raise CantSendEmailError() from e

    def post(self, body):
        if 'email_confirm_token' in body:
            body = decode_token(body['email_confirm_token'], secret=settings.EMAIL_JWT_KEY)
            pwd = body.pop('password')
            body['password_hash'], body['salt'] = hash_password(pwd)
            usr = User.create(**body)
            # TODO защититься от ошибок уникальности логина в бд
            return {'id': usr.id}, 201

        usr = User.get_or_none(login=body['login'])
        if usr is not None:
            abort(409, "Login exists")

        token = encode_token(
            body,
            secret=settings.EMAIL_JWT_KEY, 
            iss=settings.SERVICE_NAME,
            exp=time() + settings.EMAIL_LINK_LIFETIME,
            iat=time(),
        )
        # TODO тут лучше сделать вайтлист retpath'ов чтобы левые ссылки от нашего имени не отправлялись
        self._send_reg_email(body['email'], body['retpath'], token)
        return {'status': 'Confirmation link sent to email'} 

    def put(self, body, user, token_info, id=None):
        if id is None and type(user) is User:
            usr, id = user, user.id
        else:
            usr = get_object_or_404(User, (User.id == id))
        
        if (
            type(user) is User and id == user.id or
            type(user) is Operator and operator.is_admin and id is not None
        ):
            User.set_by_id(id, body)
            return NoContent
        abort(403)

    def delete(self, user, token_info, id=None):
        if id is None and type(user) is User:
            usr, id = user, user.id
        else:
            usr = get_object_or_404(User, (User.id == id))

        if (
            type(user) is User and id == user.id or
            type(user) is Operator and user.is_admin
        ):
            usr.delete_instance()
            return NoContent
        abort(403)
        

    def get(self, user, token_info, id=None):
        if id is None and type(user) is User:
            usr_by_id, id = user, user.id
        else:
            usr_by_id = get_object_or_404(User, (User.id == id))

        if (
            type(user) is Operator and id in user.allowed or
            type(user) is Operator and user.is_admin or
            type(user) is User and user.id == id
        ):
            return usr_by_id.serialize()
        abort(403)
