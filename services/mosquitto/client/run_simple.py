from datetime import datetime
import json
import logging
import sys
import traceback
import clickhouse_connect as clickhouse
from argparse import ArgumentParser

# Конфигурация ClickHouse
CH_HOST = 'clickhouse'
CH_USER = "mqttUser"
CH_PASSWORD = "resUttqm"
CH_DATABASE = 'IoMT_DB'
CH_TABLENAME_FORMAT = '{user_id}/{mac}/{freq}'
CH_SESSIONS_FORMAT = 'sessions_{user_id}/{mac}/{freq}'

# Настройка логгера
log = logging.getLogger(__name__)

def configure_logger(logger):
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)-5s %(name)-12s [%(asctime)s] %(message)s')
    logger.addHandler(handler)
    handler.setFormatter(formatter)

class FileProcessor:
    def __init__(self):
        self.user_sessions = dict()
        self.clh_client = None
        
    def connect_clickhouse(self):
        """Установка соединения с ClickHouse"""
        self.clh_client = clickhouse.get_client(
            host=CH_HOST,
            user=CH_USER,
            password=CH_PASSWORD,
            database=CH_DATABASE,
            client_name=CH_USER,
        )
    
    def process_file(self, file_path):
        """Основной метод обработки файла"""
        self.connect_clickhouse()
        
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                try:
                    # Ожидаем формат: topic|json_payload
                    if '|' not in line:
                        log.warning(f"Invalid format in line {line_num}, skipping")
                        continue
                        
                    topic, payload = line.split('|', 1)
                    self.process_message(topic, payload)
                    
                except Exception as e:
                    log.error(f"Error processing line {line_num}: {e}")
                    log.error(traceback.format_exc())
    
    def process_message(self, topic, payload):
        """Обработка одного сообщения"""
        log.debug(f"Processing topic: {topic}, payload: {payload[:100]}...")
        
        # Парсинг topic
        topic_parts = topic.split('/', 4)
        if len(topic_parts) != 5:
            log.error(f"Invalid topic format: {topic}")
            return
            
        _, user_id, mac, freq, flag = topic_parts
        
        # Парсинг payload
        try:
            data = json.loads(payload)
            values = data["value"].strip("[]").split(",")
            timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S.%f")
            data_points = [(timestamp, int(x)) for x in values]
        except Exception as e:
            log.error(f"Error parsing payload: {e}")
            return

        # Подготовка имен таблиц
        table = CH_TABLENAME_FORMAT.format(user_id=user_id, mac=mac, freq=freq)
        sessions_table = CH_SESSIONS_FORMAT.format(user_id=user_id, mac=mac, freq=freq)

        # Создание таблиц (если не существуют)
        self.create_tables(table, sessions_table)

        # Запись данных
        self.insert_data(table, data_points)

        # Обработка флагов сессии
        self.handle_session_flags(flag, sessions_table, data_points)

    def create_tables(self, data_table, sessions_table):
        """Создание таблиц в ClickHouse при необходимости"""
        try:
            self.clh_client.command(
                """
                CREATE TABLE IF NOT EXISTS {table_name:Identifier} 
                (timestamp DateTime64 CODEC(DoubleDelta, LZ4), value Int32 CODEC(T64, LZ4))
                ENGINE = MergeTree()
                ORDER BY timestamp
                """,
                parameters=dict(table_name=data_table),
            )
            
            self.clh_client.command(
                """
                CREATE TABLE IF NOT EXISTS {table_name:Identifier} 
                (begin DateTime64 CODEC(DoubleDelta, LZ4), end DateTime64 CODEC(DoubleDelta, LZ4))
                ENGINE = MergeTree()
                ORDER BY begin
                """,
                parameters=dict(table_name=sessions_table),
            )
        except Exception as e:
            log.error(f"Error creating tables: {e}")
            raise

    def insert_data(self, table, data):
        """Вставка данных в ClickHouse"""
        try:
            self.clh_client.insert(
                table=f"`{table}`",
                data=data,
                settings={'async_insert': True},
            )
            log.debug(f"Inserted {len(data)} rows into {table}")
        except Exception as e:
            log.error(f"Error inserting data into {table}: {e}")
            raise

    def handle_session_flags(self, flag, sessions_table, data_points):
        """Обработка флагов сессии"""
        try:
            if flag == "0":  # Начало сессии
                self.user_sessions[sessions_table] = data_points[0][0]
                
            elif flag == "2":  # Конец сессии
                if sessions_table not in self.user_sessions:
                    log.warning(f"No session start for {sessions_table}")
                    return
                    
                self.clh_client.insert(
                    table=f"`{sessions_table}`",
                    data=[(self.user_sessions[sessions_table], data_points[0][0])],
                    settings={'async_insert': True},
                )
                del self.user_sessions[sessions_table]
                
            elif flag == "3":  # Одновременно начало и конец
                self.clh_client.insert(
                    table=f"`{sessions_table}`",
                    data=[(data_points[0][0], data_points[-1][0])],
                    settings={'async_insert': True},
                )
        except Exception as e:
            log.error(f"Error handling session flag {flag}: {e}")
            raise

def main():
    # Парсинг аргументов командной строки
    parser = ArgumentParser(description='Process ECG data from file to ClickHouse')
    parser.add_argument('file_path', help='Path to input data file')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    args = parser.parse_args()

    # Настройка логгера
    configure_logger(log)
    log.setLevel(args.log_level)

    # Обработка файла
    processor = FileProcessor()
    try:
        log.info(f"Starting processing file: {args.file_path}")
        processor.process_file(args.file_path)
        log.info("Processing completed successfully")
    except Exception as e:
        log.error(f"Fatal error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()



# from datetime import datetime
# import json
# import logging
# import time
# from paho.mqtt import subscribe
# from paho.mqtt.client import MQTTv5
# import requests
# import sys
# import ssl
# import traceback
# import clickhouse_connect as clickhouse

# API_ADMIN_LOGIN = 'root'
# API_ADMIN_PASSWORD = 'toor'
# API_USERNAME = "mqttUser"
# API_PASSWORD = "resUttqm"
# API_BASE = "http://nginx/api/v1"

# MQTT_QOS = 2
# MQTT_BROKER_HOSTNAME = 'localhost'
# MQTT_BROKER_PORT = 1883
# MQTT_CLIENT_ID = 'DBWriter'
# MQTT_SUBSCRIBE_TOPICS = [
#     'ecg/#',
# ]

# CH_HOST = 'clickhouse'
# CH_USER = API_USERNAME
# CH_PASSWORD = API_PASSWORD
# CH_DATABASE = 'IoMT_DB'
# CH_TABLENAME_FORMAT = '{user_id}/{mac}/{freq}'
# CH_SESSIONS_FORMAT = 'sessions_{user_id}/{mac}/{freq}'

# RETRY_COUNT = 9
# RETRYBLE = {502}

# log = logging.getLogger(__name__)
# def configure_logger(logger):
#     logger.setLevel(logging.DEBUG)
#     handler = logging.StreamHandler(sys.stdout)
#     formatter = logging.Formatter('%(levelname)-5s %(name)-12s [%(asctime)s] %(message)s')
#     logger.addHandler(handler)
#     handler.setFormatter(formatter)

# def request_with_retries(*args, **kwargs):
#     try_num = 0
#     while try_num < RETRY_COUNT:
#         r = requests.post(*args, **kwargs)
#         if r.status_code in RETRYBLE:
#             try_num += 1
#             log.warning(f"Request failed. Retry number {try_num}. Sleep for {2**try_num} seconds.")
#             time.sleep(2**try_num)
#         else:
#             break
#     else:
#         log.error("Request failed permanently. Give up.")
#     return r

# def register_operator(admin_username, admin_password,
#                       login, password):
#     auth = requests.auth.HTTPBasicAuth(admin_username, admin_password)
#     r = request_with_retries(API_BASE + "/auth/operator", auth=auth)
#     if not r.ok:
#         log.error(f"Unable to get JWT token for administrator. Status: {r.status_code} message: \"{r.text}\"")
#         exit(1)
#     token = r.json()['token']
#     del r
#     r = request_with_retries(
#         API_BASE + "/operator", 
#         headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
#         data=json.dumps(dict(
#             login=login,
#             password=password,
#         )),
#     )
#     del token
#     if r.ok:
#         log.debug("Operator registered")
#     elif r.status_code == 409:
#         log.debug("Operator exist")
#     else:
#         log.error(f"Can't create operator. Status {r.status_code} message: \"{r.text}\"")
#         exit(1)


# def get_token(username, password):
#     auth = requests.auth.HTTPBasicAuth(username, password)
#     r = request_with_retries(API_BASE + "/auth/operator", auth=auth)
#     if not r.ok:
#         log.error(f"Unable to get JWT token. Status: {r.status_code} message: \"{r.text}\"")
#         exit(1)
#     data = r.json()
#     log.info(f"Got token ***{data['token'][-10:]}")
#     return data['token']

# def process_msg(client, userdata, message):
#     client.enable_logger(log)
#     # TODO здесь надо бы проверрить что пользователь не пишет в чужую таблицу
#     # ecg/1/F6:A1:DC:98:19:CF/frequency/flag : b'{"value":"67","timestamp":"2023-04-22T11:33:48.825011"}'
#     # flag: {0: begin session, 1: continue session, 2: end session, 3: start+end}
#     topic_info = message.topic.split('/', 4)
#     log.info(message.topic)
#     log.info(message.payload)
#     if len(topic_info) != 5:
#         log.error(f"Unknown topic format: {message.topic}")
#         return
#     _, user_id, mac, freq, flag = topic_info
#     data = json.loads(message.payload)
#     data["value"] = data["value"].strip("[]").split(",")
#     try:
#         data = list((datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S.%f"), int(x)) for x in data["value"])
#     except Exception as e:
#         log.error(traceback.format_exception(e))
#         return

#     # если нет таблицы - создать таблицу
#     table = CH_TABLENAME_FORMAT.format(
#         user_id=user_id,
#         mac=mac,
#         freq=freq
#     )
#     sessions_table = CH_SESSIONS_FORMAT.format(
#         user_id = user_id,
#         mac=mac,
#         freq=freq
#     )
#     clh_client = clickhouse.get_client(
#         host=CH_HOST,
#         user=CH_USER,
#         password=CH_PASSWORD,
#         database=CH_DATABASE,
#         client_name=CH_USER,
#     )
#     clh_client.command(
#         """
#         CREATE TABLE IF NOT EXISTS {table_name:Identifier} 
#         (timestamp DateTime64 CODEC(DoubleDelta, LZ4), value Int32 CODEC(T64, LZ4))
#         Engine MergeTree
#         ORDER BY timestamp
#         """,
#         parameters=dict(table_name=table),
#     )
#     clh_client.command(
#         """
#         CREATE TABLE IF NOT EXISTS {table_name:Identifier} 
#         (begin DateTime64 CODEC(DoubleDelta, LZ4), end DateTime64 CODEC(DoubleDelta, LZ4))
#         Engine MergeTree
#         ORDER BY begin
#         """,
#         parameters=dict(table_name=sessions_table),
#     )

#     # записать данные
#     clh_client.insert(
#         table=f"`{table}`",
#         data=data,
#         settings={'async_insert': True},
#     )

#     if flag == "0":
#         user_sessions[sessions_table] = data[0][0]
#     if flag == "2":
#         if user_sessions.get(sessions_table, None) is None:
#             log.info(f"There was no initial packet for {user_id} session")
#             return
#         clh_client.insert(
#             table=f"`{sessions_table}`",
#             data=[
#                 (user_sessions[sessions_table], data[0][0]),
#             ],
#             settings={'async_insert': True},
#         )
#         del user_sessions[sessions_table]
#     if flag == "3":
#         clh_client.insert(
#             table=f"`{sessions_table}`",
#             data=[
#                 (data[0][0], data[-1][0]),
#             ],
#             settings={'async_insert': True},
#         )

#     log.info("%s" % client)
#     log.info("userdata=%s" % userdata)

# if __name__ == "__main__":
#     user_sessions = dict()
#     configure_logger(log)
#     register_operator(
#         admin_username=API_ADMIN_LOGIN,
#         admin_password=API_ADMIN_PASSWORD,
#         login=API_USERNAME, 
#         password=API_PASSWORD,
#     )
#     while True:
#         token = get_token(API_USERNAME, API_PASSWORD)
#         # TODO что если токен протух
#         subscribe.callback(
#             callback=process_msg, 
#             topics=MQTT_SUBSCRIBE_TOPICS, 
#             qos=MQTT_QOS,
#             hostname=MQTT_BROKER_HOSTNAME,
#             port=MQTT_BROKER_PORT,
#             client_id=MQTT_CLIENT_ID,
#             auth=dict(
#                 username=token,
#                 password=token,
#             ),
#             protocol=MQTTv5,
#             clean_session=None
#         )
