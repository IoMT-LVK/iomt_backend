raw_env = "FLASK_CONFIG=./flask_config.cfg"
workers = 3
bind = "0.0.0.0:5000"
umask = 7  # 007
# errorlog = "/home/kh9iz/iomt-project/gunicorn.log"
loglevel = "DEBUG"
reload = True
wsgi_app = "app:app"
