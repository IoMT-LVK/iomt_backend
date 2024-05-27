from datetime import datetime
import json
import logging
import time
from paho.mqtt import subscribe
from paho.mqtt.client import MQTTv5
import requests
import sys
import ssl
import traceback
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
    'ecg/#',
]

CH_HOST = 'clickhouse'
CH_USER = API_USERNAME
CH_PASSWORD = API_PASSWORD
CH_DATABASE = 'IoMT_DB'
CH_TABLENAME_FORMAT = '{user_id}/{mac}/{freq}'
CH_SESSIONS_FORMAT = 'sessions_{user_id}/{mac}/{freq}'

RETRY_COUNT = 9
RETRYBLE = {502}

log = logging.getLogger(__name__)
def configure_logger(logger):
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)-5s %(name)-12s [%(asctime)s] %(message)s')
    logger.addHandler(handler)
    handler.setFormatter(formatter)

def request_with_retries(*args, **kwargs):
    try_num = 0
    while try_num < RETRY_COUNT:
        r = requests.post(*args, **kwargs)
        if r.status_code in RETRYBLE:
            try_num += 1
            log.warning(f"Request failed. Retry number {try_num}. Sleep for {2**try_num} seconds.")
            time.sleep(2**try_num)
        else:
            break
    else:
        log.error("Request failed permanently. Give up.")
    return r

def register_operator(admin_username, admin_password,
                      login, password):
    auth = requests.auth.HTTPBasicAuth(admin_username, admin_password)
    r = request_with_retries(API_BASE + "/auth/operator", auth=auth)
    if not r.ok:
        log.error(f"Unable to get JWT token for administrator. Status: {r.status_code} message: \"{r.text}\"")
        exit(1)
    token = r.json()['token']
    del r
    r = request_with_retries(
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
    r = request_with_retries(API_BASE + "/auth/operator", auth=auth)
    if not r.ok:
        log.error(f"Unable to get JWT token. Status: {r.status_code} message: \"{r.text}\"")
        exit(1)
    data = r.json()
    log.info(f"Got token ***{data['token'][-10:]}")
    return data['token']

def process_msg(client, userdata, message):
    client.enable_logger(log)
    # TODO здесь надо бы проверрить что пользователь не пишет в чужую таблицу
    # ecg/1/F6:A1:DC:98:19:CF/frequency/flag : b'{"value":"67","timestamp":"2023-04-22T11:33:48.825011"}'
    # flag: {0: begin session, 1: continue session, 2: end session, 3: start+end}
    topic_info = message.topic.split('/', 4)
    log.info(message.topic)
    log.info(message.payload)
    if len(topic_info) != 5:
        log.error(f"Unknown topic format: {message.topic}")
        return
    _, user_id, mac, freq, flag = topic_info
    data = json.loads(message.payload)
    data["value"] = data["value"].strip("[]").split(",")
    try:
        data = list((datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S.%f"), int(x)) for x in data["value"])
    except Exception as e:
        log.error(traceback.format_exception(e))
        return

    # если нет таблицы - создать таблицу
    table = CH_TABLENAME_FORMAT.format(
        user_id=user_id,
        mac=mac,
        freq=freq
    )
    sessions_table = CH_SESSIONS_FORMAT.format(
        user_id = user_id,
        mac=mac,
        freq=freq
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
        (timestamp DateTime64 CODEC(DoubleDelta, LZ4), value Int32 CODEC(T64, LZ4))
        Engine MergeTree
        ORDER BY timestamp
        """,
        parameters=dict(table_name=table),
    )
    clh_client.command(
        """
        CREATE TABLE IF NOT EXISTS {table_name:Identifier} 
        (begin DateTime64 CODEC(DoubleDelta, LZ4), end DateTime64 CODEC(DoubleDelta, LZ4))
        Engine MergeTree
        ORDER BY begin
        """,
        parameters=dict(table_name=sessions_table),
    )

    # записать данные
    clh_client.insert(
        table=f"`{table}`",
        data=data,
        settings={'async_insert': True},
    )

    if flag == "0":
        user_sessions[sessions_table] = data[0][0]
    if flag == "2":
        if user_sessions.get(sessions_table, None) is None:
            log.info(f"There was no initial packet for {user_id} session")
            return
        clh_client.insert(
            table=f"`{sessions_table}`",
            data=[
                (user_sessions[sessions_table], data[0][0]),
            ],
            settings={'async_insert': True},
        )
        del user_sessions[sessions_table]
    if flag == "3":
        clh_client.insert(
            table=f"`{sessions_table}`",
            data=[
                (data[0][0], data[-1][0]),
            ],
            settings={'async_insert': True},
        )

    log.info("%s" % client)
    log.info("userdata=%s" % userdata)

if __name__ == "__main__":
    user_sessions = dict()
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
            clean_session=None
        )
