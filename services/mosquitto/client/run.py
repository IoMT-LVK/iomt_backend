from paho.mqtt.client import (
    MQTTv5,
    Client,
)
import time
import logging
import json
from clickhouse_driver import Client
import jwt
from datetime import datetime
import requests

import sys
sys.path.append('..')

MQTT_CLIENT_ID = "db_writer"
MQTT_TOPIC_TO_SUBSCRIBE = "c/#"
MQTT_QOS = 2
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_KEEP_CONN_ALIVE = 60

API_USERNAME = "mqttUser"
API_PASSWORD = "resUttqm"
API_BASE = "http://rest_api/api/v1"


click_password = "iomtpassword123"

clientdb = Client(host='clickhouse', password = click_password)
insert_bulk = {}
with open("/run/secrets/jwt_key", "rt") as f:
    key = f.read()
count = 0

log = logging.getLogger(__name__)
def configure_logger(logger):
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)-5s %(name)-12s [%(asctime)s] %(message)s')
    logger.addHandler(handler)
    handler.setFormatter(formatter)

    

def get_token():
    auth = requests.auth.HTTPBasicAuth(API_USERNAME, API_PASSWORD)
    r = requests.post(API_BASE + "/auth/user", auth=auth)
    if not r.ok:
        exit(1)
    data = r.json()
    return data['token']

def token():
    t = {
        "sub": "mqttUser",
        "iat": int(datetime.timestamp(datetime.now())),
        "exp": int(datetime.timestamp(datetime.now())) + 60 * 60 * 24 * 30 * 12,
        "subs": ["c/#"],
        "publ": ["s/#"]
    }
    return jwt.encode(t, key, algorithm="HS256")


class DBWriterClient(Client):

    def __init__(
        self, 
        client_name='', 
        subscribed_to=MQTT_TOPIC_TO_SUBSCRIBE, 
        broker_host=MQTT_BROKER_HOST,
        broker_port=MQTT_BROKER_PORT,
        keep_conn_alive=MQTT_KEEP_CONN_ALIVE,
    ):
        super().__init__(
            client_id=client_name,
            clean_session=False,
            protocol=MQTTv5,
        )
        self.api_token = get_token()
        self.username_pw_set(
            username=api_token, 
            password=api_token,
        )

        self.topic = topic_name
        self.qos = MQTT_QOS
        self.host = broker_host
        self.port = broker_port
        self.keep_conn_alive = keep_conn_alive

    def connect(self):
        super().connect(
            self.host, 
            port=self.port,
            keepalive=self.keep_conn_alive,
        )

    def on_connect(self, pvtClient, userdata, flags, rc):
        if (rc == 0):
            log.info("Connected! Return Code:" + str(rc))
            result = self.client.subscribe(self.topic, self.qos)
        elif (rc == 5):
            log.error("Authentication Error! Return Code: " + str(rc))
            self.client.disconnect()

    def on_disconnect(self, client, userdata, rc):
        token = get_token()
        self.client.username_pw_set(username=token, password=token)

    def on_log(self, opic, userdata, level, buf):
        log.info("Logs: " + str(buf))

    def on_message(self, pvtClient, userdata, msg):
        log.info("Gotcha")
        global insert_bulk, count
        data = msg.payload.decode()
        topic = msg.topic                   # c/username/device/data

        count += 1

        usr_device = topic.split('/')[1] + '_' + topic.split('/')[2].replace(':', '')
        log.info(usr_device)

        data = json.loads(data)

        log.info(str(count) + str(data))
        if usr_device not in insert_bulk.keys():
            insert_bulk[usr_device] = []

        data['Clitime'] = datetime.strptime(data["Clitime"], '%Y-%m-%d %H:%M:%S')

        insert_bulk[usr_device].append(data)

        if len(insert_bulk[usr_device]) == 1:

            res = clientdb.execute(
                'insert into ' + usr_device + ' (Clitime, Millisec, HeartRate, RespRate, Insp, Exp, Steps, Activity, Cadence) values',
                insert_bulk[usr_device])

            log.info(res)
            if res == 1:
                log.info("insert success")
            else:
                log.error("bad insert")
            insert_bulk[usr_device] = []


def run():
    climqtt = DBWriterClient(client_name=MQTT_CLIENT_ID)
    climqtt.connect()
    climqtt.loop_forever()


if __name__ == '__main__':
    configure_logger(log)
    log.info("started")
    run()
