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
1. [Create secrets](/secrets/README.md)
   You can do it manually: `export DB_PASSWORD=qwerty`
   or by .env file: `echo 'DB_PASSWORD=qwerty' > .env`
   List of required env vars available in `secrets` root module of [docker-compose.yaml](docker_compose.yaml).
1. Start services
   `docker compose up --build`
