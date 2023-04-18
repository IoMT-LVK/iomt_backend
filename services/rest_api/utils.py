import os
from connexion.jsonifier import JSONEncoder
import jwt
import hashlib
from email.message import EmailMessage
from smtplib import SMTP_SSL
from flask import request

import dev_settings as settings
from models import (
    User,
    Operator,
)


def encode_token(data={}, secret=settings.JWT_KEY, **extra):
    return jwt.encode(data | extra, secret, algorithm='HS256')

def decode_token(token, secret=settings.JWT_KEY):
    return jwt.decode(token, secret, algorithms=['HS256'])

def jwt_auth(token):
    # TODO Что если токен просрочен или не валидный?
    # или пользователь токена удален
    token_info = decode_token(token)
    if token_info is None:
        return None
    type, id = token_info['sub'].split('/', 1)
    if type == 'user':
        token_info['sub'] = User.get_by_id(id)
    elif type == 'operator':
        token_info['sub'] = Operator.get_by_id(id)
    else:
        raise ValueError()
    return token_info


def basic_user_auth(username, password):
    usr = User.get_or_none(login=username)
    if usr is None:
        return None
    pwd_hash, _ = hash_password(password, usr.salt)
    if usr.password_hash == pwd_hash:
        return {'sub': usr}
    return None

def basic_operator_auth(username, password):
    usr = Operator.get_or_none(login=username)
    if usr is None:
        return None
    pwd_hash, _ = hash_password(password, usr.salt)
    if usr.password_hash == pwd_hash:
        return {'sub': usr}
    return None

def send_email(subject, text, to):
    msg = EmailMessage()
    msg.set_content(text)
    msg['Subject'] = subject
    msg['From'] = settings.MAIL_ADDRESS
    msg['To'] = to
    
    server_ssl = SMTP_SSL(settings.MAIL_SERVER,  settings.MAIL_PORT)
    server_ssl.login(settings.MAIL_ADDRESS, settings.MAIL_PASSWORD)
    server_ssl.send_message(msg)
    server_ssl.close()

def hash_password(pwd, salt=None):
    if len(pwd) > settings.PASSWORD_MAX_LEN:
        raise ValueError()
    salt = salt or os.urandom(settings.PASSWORD_HASH_SALT_LEN)
    pwd_hash = hashlib.scrypt(
        pwd.encode(),
        salt=salt,
        n=settings.PASSWORD_HASH_COST,
        r=settings.PASSWORD_HASH_BLOCK_SIZE,
        p=settings.PASSWORD_HASH_PARALLEL,
        dklen=settings.PASSWORD_HASH_LEN,
    )
    return pwd_hash, salt

                                           
class SerializeJSONEncoder(JSONEncoder):   
    def default(obj):                      
        try:                               
            serialized = obj.serialize()   
        except AttributeError:
            pass
        else:
            return serialized
        return super().default(obj)
