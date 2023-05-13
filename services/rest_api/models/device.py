from peewee import (
    AutoField,
    FixedCharField,
    ForeignKeyField,
)

from .base import BaseModel
from . import (
    User,
    DeviceType,
)


class Device(BaseModel):
    id = AutoField()

    user = ForeignKeyField(
        User,
        backref='devices',
        null=False,
        index=True,
    )
    device_type = ForeignKeyField(
        DeviceType,
        backref='users',
        null=False,
    )
    mac = FixedCharField(  # TODO сделать кастомное поле для MAC адресов
        max_length=20,
        null=False,
        unique=False,
    )

    def serialize(self):
        srlz = super().serialize()
        srlz['user_id'] = srlz.pop('user')
        srlz['device_type_id'] = srlz.pop('device_type')
        return srlz
