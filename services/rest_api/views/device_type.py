import re
from connexion import NoContent
from flask.views import MethodView

hexoskin = {
    "id": 0,
    "general": {
        "name": "Hexoskin",
        "name_regex": "HX-(\\d)+",
        "type": "vest",
    },
    "characteristics": {
        "heartRate": {
            "name": "Heart Rate",
            "service_uuid": "0000180d-0000-1000-8000-00805f9b34fb",
            "sensor_uuid": "00002a37-0000-1000-8000-00805f9b34fb",
        },
        "respirationRate": {
            "name": "Respiration Rate",
            "service_uuid": "3b55c581-bc19-48f0-bd8c-b522796f8e24",
            "sensor_uuid": "9bc730c3-8cc0-4d87-85bc-573d6304403c",
        },
        "accelerometerRate": {
            "name": "Accelerometer Rate",
            "service_uuid": "bdc750c7-2649-4fa8-abe8-fbf25038cda3",
            "sensor_uuid": "75246a26-237a-4863-aca6-09b639344f43",
        },
    },
}

odlid = {
    "id": 1,
    "general": {
        "name": "Mi Band",
        "name_regex": ".*",
        "type": "bracelet"
    },
    "characteristics": {
        "heartRate": {
            "name": "Heart Rate",
            "service_uuid": "0000180d-0000-1000-8000-00805f9b34fb",
            "sensor_uuid": "00002a37-0000-1000-8000-00805f9b34fb"
        }
    }
}


class DeviceTypeView(MethodView):

    def post(self, user, token_info):
        print(self.post.__qualname__)
        return {'id': 1} 

    def put(self, user, token_info):
        print(self.put.__qualname__)
        return NoContent

    def delete(self, user, token_info):
        print(self.delete.__qualname__)
        return NoContent

    def get(self, id, user=None, token_info=None):
        print(self.get.__qualname__)
        return hexoskin


class DeviceTypesView(MethodView):
    def get(self, user=None, token_info=None, name=None):
        if name is None:
            return [hexoskin, odlid]
        return [
            i 
            for i in (hexoskin, odlid)
            if re.search(name, i['general']['name'])
        ]


__all__ = [
    "DeviceTypeView",
    "DeviceTypesView",
]
