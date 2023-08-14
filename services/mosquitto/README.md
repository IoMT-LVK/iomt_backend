### MQTT part of project
This services consist of two processes:
- broker
- client

## Broker
Broker supports delivery of messages.

It built on eclipse mosquitto technology and secured by go-auth plugin.
Authentification implemented by JWT from rest\_api service.
To authorize send token in **username** field and something in password field (plugin specific schema).


## Client
Client subscribes to topics starting with `c` letter.

