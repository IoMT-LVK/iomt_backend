import paho.mqtt.client as mqtt
import daemon.pidfile
import time
import logging
import json
from clickhouse_driver import Client

import sys
sys.path.append('..')

from web.sensors import get_sensors

clientdb = Client(host='localhost')
topicName = "c/#"
host = "localhost"
QOS_val = 2
insert_bulk = {}


class MQTT_Client:

    def __init__(self, topic_name, qos_val, broker_host):
        self.client = mqtt.Client()
        self.topic = topic_name
        self.qos = qos_val
        self.host = broker_host
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_log = self.on_log

    def loop(self):
        self.client.connect(self.host)
        time.sleep(2)
        self.client.loop_forever()

    def on_connect(self, pvtClient, userdata, flags, rc):
        if (rc == 0):
            logger.info("Connected! Return Code:" + str(rc))
            result = self.client.subscribe(self.topic, self.qos)

        elif (rc == 5):
            logger.error("Authentication Error! Return Code: " + str(rc))
            self.client.disconnect()

    def on_log(self, opic, userdata, level, buf):
        logger.info("Logs: " + str(buf))

    def on_message(self, pvtClient, userdata, msg):
        global insert_bulk
        data = msg.payload.decode()
        topic = msg.topic                   # s/username_device/data
        logger.info(topic)

        usr_device = topic.split('/')[1]

        data = json.loads(data)
        # data['Millisec'] = data['Clitime'].split('.')[1]
        # data['Clitime'] = data['Clitime'].split('.')[0]
        # data["Clitime"] = datetime.datetime.strptime(data["Clitime"], '%Y-%m-%d %H:%M:%S')

        if usr_device not in insert_bulk.keys():
            insert_bulk[usr_device] = []

        insert_bulk[usr_device].append(data)

        if len(insert_bulk[usr_device]) > 1000:

            sensors = get_sensors(usr_device)
            #res = clientdb.execute("insert into {} ({}) values".format(usr_device, sensors), insert_bulk[usr_device])

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

    with daemon.DaemonContext(
            stdout=handler.stream,
            stderr=handler.stream,
            pidfile=daemon.pidfile.PIDLockFile('/var/run/mydaemon/dbpid.pid'),
            files_preserve=[handler.stream]
    ) as context:
        run()
