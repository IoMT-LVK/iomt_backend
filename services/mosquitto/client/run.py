import paho.mqtt.client as mqtt
import time
import logging
import json
from clickhouse_driver import Client
import jwt
from datetime import datetime

import sys
sys.path.append('..')

click_password = "iomtpassword123"

clientdb = Client(host='clickhouse', password = click_password)
topicName = "c/#"
host = "localhost"
QOS_val = 2
insert_bulk = {}
with open("/run/secrets/jwt_key", "rt") as f:
    key = f.read()
count = 0

def token():
    t = {
        "sub": "mqttUser",
        "iat": int(datetime.timestamp(datetime.now())),
        "exp": int(datetime.timestamp(datetime.now())) + 311000000,
        "subs": ["c/#"],
        "publ": ["s/#"]
    }
    return jwt.encode(t, key, algorithm="HS256")


class MQTT_Client:

    def __init__(self, topic_name, qos_val, broker_host):
        self.client = mqtt.Client()
        self.topic = topic_name
        self.qos = qos_val
        self.host = broker_host
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_log = self.on_log
        self.client.username_pw_set(username="", password=token())

    def loop(self):
        self.client.connect(self.host, port=1883)
        time.sleep(2)
        self.client.loop_forever()

    def on_connect(self, pvtClient, userdata, flags, rc):
        if (rc == 0):
            logger.info("Connected! Return Code:" + str(rc))
            result = self.client.subscribe(self.topic, self.qos)
        elif (rc == 5):
            logger.error("Authentication Error! Return Code: " + str(rc))
            self.client.disconnect()

    def on_disconnect(self, client, userdata, rc):
        self.client.username_pw_set(username="", password=token())

    def on_log(self, opic, userdata, level, buf):
        logger.info("Logs: " + str(buf))

    def on_message(self, pvtClient, userdata, msg):
        logger.info("Gotcha")
        global insert_bulk, count
        data = msg.payload.decode()
        topic = msg.topic                   # c/username/device/data

        count += 1

        usr_device = topic.split('/')[1] + '_' + topic.split('/')[2].replace(':', '')
        logger.info(usr_device)

        data = json.loads(data)

        logger.info(str(count) + str(data))
        if usr_device not in insert_bulk.keys():
            insert_bulk[usr_device] = []

        data['Clitime'] = datetime.strptime(data["Clitime"], '%Y-%m-%d %H:%M:%S')

        insert_bulk[usr_device].append(data)

        if len(insert_bulk[usr_device]) == 1:

            res = clientdb.execute(
                'insert into ' + usr_device + ' (Clitime, Millisec, HeartRate, RespRate, Insp, Exp, Steps, Activity, Cadence) values',
                insert_bulk[usr_device])

            logger.info(res)
            if res == 1:
                logger.info("insert success")
            else:
                logger.error("bad insert")
            insert_bulk[usr_device] = []


def run():
    climqtt = MQTT_Client(topicName, QOS_val, host)
    climqtt.loop()


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('logger.log')
    formatter = logging.Formatter('%(levelname)-5s %(name)-12s [%(asctime)s] %(message)s')
    logger.addHandler(handler)
    handler.setFormatter(formatter)

    logger.info("started")

    
    run()
