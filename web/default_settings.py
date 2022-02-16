# This is default settings for IoMT service

# Don't change this if you want to configure your application
# Instead create or change config file in 'config' folder
# and write to env var FLASK_CONFIG absolute path to your file

# Note: for gunicorn instance you could do it by --env FLASK_CONFIG=/path/to/file

MAIL_SERVER = '< example.com >'
MAIL_USERNAME = '< YourUsername@example.com >'
MAIL_PASSWORD = '< your password >'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USE_TLS = False

MONGODB_DB = 'data'
MONGODB_HOST = 'localhost'

CLICKHOUSE_PASS = '< chpass >'

SECRET_KEY='mus7_b3_chan9ed'
