import re
from connexion import NoContent

from .base import BaseView
from models import (
    DeviceType,
    Operator,
)

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

class DeviceTypeView(BaseView):

    def _get_or_create_characteristics(self, chars):
        # Вернем ошибку если такой slug уже есть
        processed_chars = {key: None for key in chars.keys}
        same_slug = Characteristic.select().where(
            Characteristic.slug.in_(chars.keys())
        ).execute()

        for exist_char in same_slug:
            slug = exist_char.slug
            cond_char = chars[slug]
            if (
                cond_char['service_uuid'] != exist_char.service_uuid or
                cond_char['characteristic_uuid'] != exist_char.characteristic_uuid
            ): 
                abort(409, f"Mismatch configuration for {exist_char.slug}")
            chars.pop(slug)
        
        # Вернем ошибку если есть такая пара uuidов
        # код очень страшный, но ничего лучше не придумал
        # TODO переделать на какие-нибудь joinы или что-то подобное
        same_uuid = Characteristic.select().where(
            Characteristic.characteristic_uuid.in_(
                char['characteristic_uuid']
                for char in chars
            )
        ).execute()
        for cond_char in chars:
            for query_char in same_uuid:
                if any(
                    query_char.service_uuid == cond_char['serice_uuid'] and
                    query_char.characteristic_uuid == cond_char['characteristic_uuid']
                ):
                    abort(409, f"Conflict uuids: {cond_char.service_uuid}, {cond_char.characteristic_uuid}")
        return same_slug, chars

    def post(self, user, token_info, body):
        self._check_account_type(allow_admin=True)
        chars = body.pop('characteristics')
        exists, insert = self._get_or_insert_characteristics(body['characteristics'])

        device = DeviceType.get_or_none(
            (DeviceType.name == body['name']) |
            (DeviceType.name_regex == body['name_regex'])
        )

        if device is not None:
            abort(409, f"DeviceType {device.name} exists")

        chars = Characteristic.insert_many(chars).execute()
        device.characteristics = chars
        device.save()

        return {'id': device.id} 

    def put(self, user, token_info):
        print(self.put.__qualname__)
        return NoContent

    def delete(self, user, token_info):
        print(self.delete.__qualname__)
        return NoContent

    def get(self, id, user=None, token_info=None):
        print(self.get.__qualname__)
        return hexoskin


class DeviceTypesView(BaseView):
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
