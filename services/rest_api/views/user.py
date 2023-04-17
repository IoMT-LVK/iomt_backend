from connexion import NoContent
from flask.views import MethodView
import logging
from smtplib import SMTPException
from time import time

from models.user import User
from exceptions import (
    LoginExistsError,
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
            return {'id': usr.id}
        usr = User.get_or_none(login=body['login'])
        if usr is not None:
            raise LoginExistsError()

        token = encode_token(
            body,
            secret=settings.EMAIL_JWT_KEY, 
            iss=settings.SERVICE_NAME,
            exp=time() + settings.EMAIL_LINK_LIFETIME,
            iat=time(),
        )
        # TODO тут лучше сделать вайтлист retpath'ов чтобы левые ссылки от нашего имени не отпраылялись
        self._send_reg_email(body['email'], body['retpath'], token)
        return {'status': 'Confirmation link sent to email'} 

    def put(self, id, user, token_info):
        print(self.put.__qualname__)
        return NoContent

    def delete(self, id, user, token_info):
        print(self.delete.__qualname__)
        return NoContent

    def get(self, id, user, token_info):
        user = User.get_by_id(id)
        return jsonify(user)
