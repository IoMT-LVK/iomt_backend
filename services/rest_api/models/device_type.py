from peewee import (
    AutoField,
    CharField,
    SmallIntegerField,
    BooleanField,
    ManyToManyField,
)

from .base import BaseModel
from .characteristic import Characteristic


class Device(BaseModel):
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
    type = SmallIntegerField(
        null=False,
        unique=False,
    )
    characteristics = ManyToManyField(Characteristic, 'devices')

    def serialize(self):
        srlz = super().serialize()
        srlz['characteristics'] = {
            slug: char_info 
            for characteristic in self.characteristics 
            for slug, char_info in sensor.serialize().items()
        }
        return srlz
