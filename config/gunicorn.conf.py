raw_env = "FLASK_CONFIG=/home/kh9iz/iomt-project/config/flask_config.cfg"
workers = 3
bind = "unix:iomt.sock"
umask = 7  # 007
errorlog = "/home/kh9iz/iomt-project/gunicorn.log"
loglevel = "DEBUG"
reload = True
wsgi_app = "app:app"
