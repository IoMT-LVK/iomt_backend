from pathlib import Path
import logging


log = logging.getLogger(__name__)

def read_secret(secret_name, default=''):
    file = Path('/run/secrets') / secret_name
    if not file.is_file():
        log.error(f"Can't read secret {secret_name}. Path {file} doesn't exist")
        return default
    with file.open() as f:
        return f.read().strip()

DB_PASSWORD = read_secret('db_password')
JWT_KEY = read_secret('jwt_key')
EMAIL_JWT_KEY = read_secret('email_jwt_key')
ROOT_OP_PASSWORD = read_secret('root_operator_password')
MAIL_PASSWORD = read_secret('mail_password')
