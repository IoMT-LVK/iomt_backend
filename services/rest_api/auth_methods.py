import jwt

from models import (
    User,
    Operator,
    db,
)
from utils import (
    decode_token,
    with_db_connection,
    hash_password,
)

@with_db_connection
def jwt_auth(token):
    # TODO Что если или пользователь токена удален
    try:
        token_info = decode_token(token)
    except jwt.exceptions.InvalidTokenError:
        return None
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

@with_db_connection
def basic_user_auth(username, password, required_scopes):
    usr = User.get_or_none(login=username)
    if usr is None:
        return None
    pwd_hash, _ = hash_password(password, usr.salt)
    if usr.password_hash == pwd_hash:
        return {'sub': usr}
    return None

@with_db_connection
def basic_operator_auth(username, password):
    usr = Operator.get_or_none(login=username)
    if usr is None:
        return None
    pwd_hash, _ = hash_password(password, usr.salt)
    if usr.password_hash == pwd_hash:
        return {'sub': usr}
    return None
