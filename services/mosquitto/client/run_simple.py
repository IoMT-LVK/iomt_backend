import logging
from paho.mqtt import subscribe
from paho.mqtt.client import MQTTv5
import requests
import sys

API_USERNAME = "mqttUser"
API_PASSWORD = "resUttqm"
API_BASE = "http://nginx/api/v1"

MQTT_QOS = 2
MQTT_BROKER_HOSTNAME = 'localhost'
MQTT_BROKER_PORT = 1883
MQTT_CLIENT_ID = 'DBWriter'
MQTT_SUBSCRIBE_TOPICS = [
    'c/#',
]

log = logging.getLogger(__name__)
def configure_logger(logger):
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)-5s %(name)-12s [%(asctime)s] %(message)s')
    logger.addHandler(handler)
    handler.setFormatter(formatter)


def get_token(username, password):
    auth = requests.auth.HTTPBasicAuth(username, password)
    r = requests.post(API_BASE + "/auth/user", auth=auth)
    if not r.ok:
        log.error(f"Unable to get JWT token. Status: {r.status_code} message: \"{r.text}\"")
        exit(1)
    data = r.json()
    log.info(f"Got token ***{data['token'][-10:]}")
    return data['token']

def process_msg(client, userdata, message):
    client.enable_logger(log)
    log.info("%s : %s" % (message.topic, message.payload))
    log.info("%s" % client)

if __name__ == "__main__":
    configure_logger(log)
    while True:
        token = get_token(API_USERNAME, API_PASSWORD)
        # TODO что если токен протух
        subscribe.callback(
            callback=process_msg, 
            topics=MQTT_SUBSCRIBE_TOPICS, 
            qos=MQTT_QOS,
            hostname=MQTT_BROKER_HOSTNAME,
            port=MQTT_BROKER_PORT,
            client_id=MQTT_CLIENT_ID,
            auth=dict(
                username=token,
                password=token,
            ),
            protocol=MQTTv5,
            clean_session=None,
        )
