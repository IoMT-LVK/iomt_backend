from peewee import (
    AutoField,
    CharField,
    SmallIntegerField,
    BooleanField,
    ManyToManyField,
)

from .base import BaseModel
from .characteristic import Characteristic


class DeviceType(BaseModel):
    id = AutoField()

    name = CharField(
        null=False,
        index=True,
        unique=True,
        max_length=64,
    )
    name_regex = CharField(
        null=True,
        unique=True,
        max_length=128,
    )
    type = CharField(  # TODO сделать кастомное поле Enum чтобы хранить числа и на строки
        null=False,
        unique=False,
    )
    characteristics = ManyToManyField(Characteristic, 'devices')

    def serialize(self):
        srlz = dict(
            characteristics={
                slug: char_info 
                for characteristic in self.characteristics 
                for slug, char_info in characteristic.serialize().items()
            }
        )
        srlz.update(
            general=dict(
                name=self.name,
                name_regex=self.name_regex,
                type=self.type,
            ),
            id=self.id,
        )
        return srlz
