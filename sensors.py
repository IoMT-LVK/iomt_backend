from pymongo import MongoClient

host = 'localhost'
port = 27017

def get_sensors(usr_device):
    """Returns a string of table attributes with sensors of requested device"""
    global host, port
    user, device = usr_device.split('_')
    with MongoClient(host, port) as client:
        db = client.data
        collection = db.registerdevices
        record = collection.find_one({"user": user, "device_id": device})
    return record['sensors']
