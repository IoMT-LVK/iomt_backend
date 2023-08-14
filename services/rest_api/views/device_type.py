import re
from connexion import NoContent
from flask import abort
from playhouse.flask_utils import get_object_or_404

from .base import BaseView
from models import (
    Characteristic,
    DeviceType,
    Operator,
)


class DeviceTypeView(BaseView):

    def _get_exists_chars(self, chars):
        # Вернем ошибку если такой slug уже есть
        same_slug = Characteristic.select().where(
            Characteristic.slug.in_(list(chars.keys()))
        ).execute()

        for exist_char in same_slug:
            slug = exist_char.slug
            cond_char = chars[slug]
            if (
                cond_char['service_uuid'] != exist_char.service_uuid or
                cond_char['characteristic_uuid'] != exist_char.characteristic_uuid
            ): 
                abort(409, f"Mismatch configuration for {exist_char.slug}")
        
        # Вернем ошибку если есть такая пара uuidов
        # TODO изначально тут планировалась проверка уникальности пар uuidов, 
        # но потом я подумал что это не так важно если будут характеристики с одинаковыми uuidами
        return same_slug
    


    def post(self, user, token_info, body):
        """
        Создаем новый датчик
        Берем все чарсы, если есть такой, то связываем с датчиком, если нет создаем
        """
        self._check_account_type(user=user, allow_admin=True)
        body.update(body.pop('general'))  # одному богу известно зачем так сделано

        device = DeviceType.get_or_none(
            (DeviceType.name == body['name']) |
            (DeviceType.name_regex == body['name_regex'])
        )
        if device is not None:
            abort(409, f"DeviceType {device.name} exists")

        # Создаем девайс TODO: если зафейлится создание чарсы, создавать девайс тоже нужно, ищи peewee.atomic
        chars_dict = body.pop('characteristics')
        device = DeviceType.create(**body)
        exists_chars = self._get_exists_chars(chars_dict)
        new_chars_slug = set(chars_dict.keys()) - set(ch.slug for ch in exists_chars)

        Characteristic.insert_many(
            chars_dict[char_slug] | {'slug': char_slug} 
            for char_slug in new_chars_slug
        ).execute()
        chars = Characteristic.select().where(
            Characteristic.slug.in_(list(chars_dict.keys()))
        ).execute()  # TODO этот запрос излишен
        device.characteristics = list(chars)
        device.save()

        return {'id': device.id} 

    def put(self, user, token_info):
        self._check_account_type(user=user, allow_admin=True)
        abort(501)  # TODO to do
        print(self.put.__qualname__)
        return NoContent

    def delete(self, user, token_info, id):
        self._check_account_type(user=user, allow_admin=True)
        dt = get_object_or_404(DeviceType, (DeviceType.id == id))
        dt.characteristics.clear()  # TODO тут в идеале надо чистить чарсы если нет связанных девайсов
        dt.delete_instance()
        return NoContent

    def get(self, id, user=None, token_info=None):
        self._check_account_type(user=user, allow_operator=True, allow_user=True)
        
        dt = get_object_or_404(DeviceType, (DeviceType.id == id))

        return dt.serialize()


class DeviceTypesView(BaseView):
    def get(self, user=None, token_info=None, name=None):
        if name is None:
            q = DeviceType.select()
        else:
            # FIXME name == '' - ломает всё
            q = DeviceType.select().where(DeviceType.name.iregexp(name))
        return [
            i.serialize()
            for i in q
        ]


__all__ = [
    "DeviceTypeView",
    "DeviceTypesView",
]
