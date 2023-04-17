# iomt-project
Scalable server part of a project related to the Internet of medical things

Cause this application run with docker, you needs to change IP in this string to your server IP, if you don't run your app on LVK-server:
clientdb = Client(host='172.30.7.214', password = click_password)

All commands was tested on Linux (Ubuntu-18.04)

--------------------------------

# Possible improvements:
- [ ] Neat logs
- [ ] SQLAlchemy support (maybe with migration to MySQL)
- [ ] RESTful interface

--------------------------------

# About architecture
Project support *docker swarm* mode.
A swarm consists of multiple Docker hosts. In this case there is only one host running in swarm mode, but keep in mind that there could be multi-host configurations for swrm.
Under this concept lies stack (set of services)
Service is multiplied task.
Task is simple docker conteiner.

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

# Start project on clean server
All commands compatible with Debian 11

1. [Install docker](https://docs.docker.com/engine/install/)
1. [Enable "swarm mode"](https://docs.docker.com/engine/swarm/swarm-mode/)
   `docker swarm init`
1. Clone repository
   `git clone git@github.com:IoMT-LVK/iomt_backend.git`
1. Create secrets: jwt\_key
   `openssl rand -base64 32 | docker secret create jwt_key -`
1. Build images
   `docker compose build`
1. Start services
   `docker stack deploy -c docker-compose.yml iomt`

### Optional
You can create specific configurations for each node.
As an example downgrade mongo version in docker-compose.production.yml

--------------------------------

To start swarm
```
docker swarm init
```
After that uou need to create networks for swarm
```
docker network create -d overlay monitoring
docker network create -d overlay iomt
```
You need registry, because application has some user images
```
docker service create --name registry --publish published=5000,target=5000 registry:2
```
And to push these images (and you need to push them every time you change it):
```
docker-compose push
```
Then you can deploy all system to swarm
```
docker stack deploy --compose-file docker-compose.yml iomt
```
if you want to delete your swarm, then type: 
```
docker stack rm iomt
```
if you want to bring your Docker Engine out of swarm mode, then type:
```
docker swarm leave --force
```
