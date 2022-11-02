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
