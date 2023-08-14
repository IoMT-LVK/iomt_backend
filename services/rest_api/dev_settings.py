SERVICE_NAME = 'IoMT_REST'

JWT_KEY = '<same_as JWT_KEY file>'
JWT_TOKEN_LIFETIME = 3 * 30 * 24 * 60 * 60  # 3 monts

DATABASE = 'mysql://rest:TODOCHANGE@mysql:3306/IoMT_DB'
FLASKDB_EXCLUDED_ROUTES = tuple()

MAIL_SERVER = 'smtp.gmail.com'
MAIL_ADDRESS = 'iomt.confirmation@gmail.com'
MAIL_PASSWORD = 'feyplseixdsorljy'
MAIL_PORT = 465
EMAIL_JWT_KEY = '<replace_this>'
EMAIL_LINK_LIFETIME = 24 * 60 * 60

PASSWORD_MAX_LEN = 64
PASSWORD_HASH_SALT_LEN = 16
PASSWORD_HASH_LEN = 64
PASSWORD_HASH_COST = 8
PASSWORD_HASH_BLOCK_SIZE = 512
PASSWORD_HASH_PARALLEL = 4

ROOT_OP_LOGIN = 'root'
ROOT_OP_PASSWORD = 'toor'

DB_CONNECTION_RETRY_COUNT = 9

def init_app(app):
    globals().update(app.config)

#settings = namedtuple('Settings', flask_app.config)(**flask_app.config)
