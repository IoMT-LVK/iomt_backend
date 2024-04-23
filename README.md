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
1. Create secrets
   You can do it manually: `export DB_PASSWORD=qwerty`
   or by .env file: `echo 'DB_PASSWORD=qwerty' > .env`
   List of required env vars available in `secrets` root module of [docker-compose.yaml](docker_compose.yaml).
1. Start services
   `docker compose up --build`

--------------------------------

# List of available endpoints:

**BASE URL** = https://iomt.lvk.cs.msu.ru

## Endpoints for operator's interface

- /login/ - login for operator or administrator
- /users/ - list users, available for current operator (or all users, if operator is administrator)
- /\<login\>/sessions - list ECG sessions of user _\<login\>_
- /\<login\>/devices - list devices, connected to user _\<login\>_
- /select/ - data selection for displaying as a plot
- /download/ - data selection for downloading in .csv format

## Administrator's endpoints:

- /admins/ - administrators's main page
- /admins/add-operator/ - create a new operator
- /admins/delete-operator/\<login\>/ - deletes operator _\<login\>_
- /admins/add-device/ - create a new _device\_type_
- /admins/add-characteristic/ - create a new characteristic, later user for _device_ creation
- /admins/add-user/ - create a new user
- /admins/connect-user/ - add _operator_ to the user's _allowed_ list
- /admins/connect-device/ - create a new _device_ instance, connected to specified _user_

## REST endpoints:

For REST endpoints you can visit [Swagger UI page](https://iomt.lvk.cs.msu.ru/api/v1/ui/)

## MQTT messages:

### The structure of MQTT topics, accepted by _iomt.lvk.cs.msu.ru:1883_:

**_ecg/\<user\_login\>/\<MAC\>/\<frequency\>/\<flag\>_**

- **_ecg_** - sign, that incoming data is ECG data
- **_\<user\_login\>_** - login of user, whose data is sent
- **_\<MAC\>_** - MAC address of device, which measured the ECG data
- **_\<frequencty\>_** - frequency of ECG measuring
- **_\<flag\>_** - flag, needed for managing user's data recording sessions
  - **_flag_** == 0: start of data transission
  - **_flag_** == 1: continue data transmission session
  - **_flag_** == 2: end of data transmission
  - **_flag_** == 3: if data fits one MQTT packet, the flag must be both 0 and 2, therefor for this case flag = 3 was added

### The structure of MQTT data:

MQTT messages must be in a correct json structure. Example:

"[[**_timestamp: DateTime64_**, **_value: int32_**], ...]"