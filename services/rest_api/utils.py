import os
from connexion.jsonifier import JSONEncoder
import jwt
import hashlib
from email.message import EmailMessage
from smtplib import SMTP_SSL
from flask import abort
from functools import wraps

import settings
from models import (
    User,
    Operator,
    db,
)


def encode_token(data={}, secret=settings.JWT_KEY, **extra):
    return jwt.encode(data | extra, secret, algorithm='HS256')

def decode_token(token, secret=settings.JWT_KEY):
    return jwt.decode(token, secret, algorithms=['HS256'])

def with_db_connection(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        db.connect(reuse_if_open=True)
        t = f(*args, **kwargs)
        if not db.is_closed():
            db.close()
        return t
    return _wrapper

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
