import os
from connexion.jsonifier import JSONEncoder
import jwt
import hashlib
from email.message import EmailMessage
from smtplib import SMTP_SSL

import dev_settings as settings


def encode_token(data, secret=settings.JWT_KEY, **extra):
    return jwt.encode(data | extra, secret, algorithm='HS256')

def decode_token(token, secret=settings.JWT_KEY):
    return jwt.decode(token, secret, algorithms=['HS256'])

def basic_auth(username, password):
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

def hash_password(pwd):
    if len(pwd) > settings.PASSWORD_MAX_LEN:
        raise ValueError()
    salt = os.urandom(settings.PASSWORD_HASH_SALT_LEN)
    pwd_hash = hashlib.scrypt(
        pwd.encode(),
        salt=salt,
        n=settings.PASSWORD_HASH_COST,
        r=settings.PASSWORD_HASH_BLOCK_SIZE,
        p=settings.PASSWORD_HASH_PARALLEL,
        dklen=settings.PASSWORD_HASH_LEN,
    )
    return salt, pwd_hash

                                           
class SerializeJSONEncoder(JSONEncoder):   
    def default(obj):                      
        try:                               
            serialized = obj.serialize()   
        except AttributeError:
            pass
        else:
            return serialized
        return super().default(obj)

