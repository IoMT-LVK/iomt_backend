import paho.mqtt.client as mqtt
import daemon
import daemon.pidfile
import time
import logging
import datetime
import json
from clickhouse_driver import Client

clientdb = Client(host = 'localhost')
topicName = "iomt/client/#"
host = "test.mosquitto.org"
QOS_val = 2
insert_bulk = []

class MQTT_Client:

    def __init__(self, topicName, QOS_val, Host):
        self.client = mqtt.Client()
        self.topic = topicName
        self.qos = QOS_val
        self.host = Host
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_log = self.on_log

    def loop(self):
        self.client.connect(self.host)
        time.sleep(2)
        self.client.loop_forever()

    def on_connect(self, pvtClient,userdata,flags, rc):
        if(rc == 0):
            logger.info("Connected to client! Return Code:" + str(rc))
            result = self.client.subscribe(self.topic, self.qos)

        elif(rc == 5):
            logger.error("Authentication Error! Return Code: "+str(rc))
            client.disconnect()

    def on_log(self, opic, userdata, level, buf):
        logger.info("Logs: "+str(buf))

    def on_message(self, pvtClient, userdata, msg):
        data = msg.payload.decode()
        topic = msg.topic
        logger.info(topic)
        insert_bulk = []
        if(data == "exit(0)"):
            client.disconnect()

        data = json.loads(data)
        data['Millisec'] = data['Clitime'].split('.')[1]
        data['Clitime'] = data['Clitime'].split('.')[0]
        data["Clitime"] = datetime.datetime.strptime(data["Clitime"], '%Y-%m-%d %H:%M:%S')

        insert_bulk.append(data)
        if (len(insert_bulk) > 1000):
            res = clientdb.execute('insert into person_1 (Clitime, Millisec, HeartRate, RespRate, Insp, Exp, Steps, Activity, Cadence) values', insert_bulk)
            logger.info(res)
            if res == 1:
                logger.info("insert success")
            else:
                logger.error("bad insert")
            insert_bulk = []

def run():
    climqtt = MQTT_Client(topicName, QOS_val, host)
    climqtt.loop()

if __name__== '__main__':
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

