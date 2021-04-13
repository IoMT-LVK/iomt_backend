import jwt
from models import db, Users, Operators
from datetime import datetime

key = 'secret'

def check_user(login, password):
    """Check user data and generate JWT."""
    user = Users.objects(login=login).first()
    if user and user.password_valid(password):
        token = {
            "sub": "mqttUser",
            "iat": int(datetime.timestamp(datetime.now())),
            "exp": int(datetime.timestamp(datetime.now())) + 300,
            # TODO topics
            "subs": ["s/#"],
            "publ": ["c/#"]
        }
        return jwt.encode(token, key, algorithm="HS256"), 200
    else:
        return {}, 402



