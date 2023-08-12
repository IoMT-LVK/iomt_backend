from datetime import datetime
import json
import logging
from paho.mqtt import subscribe
from paho.mqtt.client import MQTTv5
import requests
import sys
import clickhouse_connect as clickhouse

API_ADMIN_LOGIN = 'root'
API_ADMIN_PASSWORD = 'toor'
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

CH_HOST = 'clickhouse'
CH_USER = API_USERNAME
CH_PASSWORD = API_PASSWORD
CH_DATABASE = 'IoMT_DB'
CH_TABLENAME_FORMAT = '{user_id}/{slug}/{mac}'

log = logging.getLogger(__name__)
def configure_logger(logger):
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)-5s %(name)-12s [%(asctime)s] %(message)s')
    logger.addHandler(handler)
    handler.setFormatter(formatter)


def register_operator(admin_username, admin_password,
                      login, password):
    auth = requests.auth.HTTPBasicAuth(admin_username, admin_password)
    r = requests.post(API_BASE + "/auth/operator", auth=auth)
    if not r.ok:
        log.error(f"Unable to get JWT token for administrator. Status: {r.status_code} message: \"{r.text}\"")
        exit(1)
    token = r.json()['token']
    del r
    r = requests.post(
        API_BASE + "/operator", 
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        data=json.dumps(dict(
            login=login,
            password=password,
        )),
    )
    del token
    if r.ok:
        log.debug("Operator registered")
    elif r.status_code == 409:
        log.debug("Operator exist")
    else:
        log.error(f"Can't create operator. Status {r.status_code} message: \"{r.text}\"")
        exit(1)


def get_token(username, password):
    auth = requests.auth.HTTPBasicAuth(username, password)
    r = requests.post(API_BASE + "/auth/operator", auth=auth)
    if not r.ok:
        log.error(f"Unable to get JWT token. Status: {r.status_code} message: \"{r.text}\"")
        exit(1)
    data = r.json()
    log.info(f"Got token ***{data['token'][-10:]}")
    return data['token']

def process_msg(client, userdata, message):
    client.enable_logger(log)
    # TODO здесь надо бы проверрить что пользователь не пишет в чужую таблицу
    # c/1/F6:A1:DC:98:19:CF/heartRate : b'{"value":"67","timestamp":"2023-04-22T11:33:48.825011"}'
    topic_info = message.topic.split('/', 3)
    if len(topic_info) != 4:
        log.error(f"Unknown topic format: {message.topic}")
        return 
    _, user_id, mac, ch_slug = topic_info
    data = json.loads(message.payload)
    try:
        user_id = int(user_id)
    except ValueError:
        log.error(f"Invalid user_id: {user_id}")
        return
    try:
        value = float(data['value'])
    except ValueError:
        log.error(f"Unknown value type: {value}")
        return
    ts = datetime.fromisoformat(data['timestamp'])

    # если нет таблицы - создать таблицу
    table = CH_TABLENAME_FORMAT.format(
        user_id=user_id,
        mac=mac,
        slug=ch_slug,
    )
    clh_client = clickhouse.get_client(
        host=CH_HOST,
        user=CH_USER,
        password=CH_PASSWORD,
        database=CH_DATABASE,
        client_name=CH_USER,
    )
    clh_client.command(
        """
        CREATE TABLE IF NOT EXISTS {table_name:Identifier} 
        (timestamp DateTime64, value Float64)
        Engine MergeTree
        ORDER BY timestamp
        """,
        parameters=dict(table_name=table),
    )

    # записать данные
    clh_client.insert(
        table=f"`{table}`",
        data=[
            (ts, value),
        ],
        settings={'async_insert': True},
    )

    log.info("%s : %s" % (message.topic, message.payload))
    log.info("%s" % client)
    log.info("userdata=%s" % userdata)
    log.debug(f"{user_id=}\t{mac=}\t{ch_slug=}\t{value=}\t{ts=}")

if __name__ == "__main__":
    configure_logger(log)
    register_operator(
        admin_username=API_ADMIN_LOGIN,
        admin_password=API_ADMIN_PASSWORD,
        login=API_USERNAME, 
        password=API_PASSWORD,
    )
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
