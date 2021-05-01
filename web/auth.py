import jwt
import os
from models import Users
from datetime import datetime

key = 'secret'

def check_user(login, password):
    """Check user data and generate JWT."""
    user = Users.objects(login=login).first()
    if not user:
        return False, {}, 402, user.user_id
    if  user.password_valid(password):
        if not user.confirmed:
            return False, {}, 200, user.user_id
        token = {
            "sub": "mqttUser",
            "iat": int(datetime.timestamp(datetime.now())),
            "exp": int(datetime.timestamp(datetime.now())) + 300,
            "subs": ["s/#"],
            "publ": ["c/" + user.user_id + "/#"]
        }
        return True, jwt.encode(token, key, algorithm="HS256"), 200, user.user_id
    else:
        return True, {}, 402, user.user_id

def check_token(token):
    try:
        jwt.decode(token, key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidSignatureError:
        return False
    return True



