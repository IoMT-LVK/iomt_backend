from clickhouse_driver import Client
from sensors import get_sensors


def create_table(name):
    clientdb = Client(host='localhost')
    sensors = get_sensors(name)

