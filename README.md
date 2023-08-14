# iomt-project
Scalable server part of a project related to the Internet of medical things

All commands was tested on Linux (Ubuntu-18.04)

--------------------------------

# Possible improvements:
- [ ] Neat logs
- [x] ORM support (maybe with migration to MySQL)
- [x] RESTful interface

--------------------------------

# Start project in compose mode
1. [Install docker](https://docs.docker.com/engine/install/)
1. Clone repository
   `git clone git@github.com:IoMT-LVK/iomt_backend.git`
1. Create secrets: jwt\_key
   `openssl rand -base64 32 | sudo tee /run/secrets/jwt_key > /dev/null`
1. Create and configure flask settings
   `cp iomt_backend/services/rest_api/settings.py /run/secrets/flask_settings.py; vim /run/secrets/flask_settings.py`
1. Build images
   `docker compose build`
1. Start services
   `docker compose up`
