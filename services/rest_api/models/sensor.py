from peewee import (
    AutoField,
    CharField,
    UUIDField,
)

from .base import BaseModel


class Sensor(BaseModel):
    id = AutoField()

    slug = CharField(
        null=False,
        index=True,
        unique=True,
        max_length=32,
    )
    name = CharField(
        null=False,
        unique=False,
        max_length=48,
    )
    service_uuid = UUIDField(
        null=False,
        unique=True,
    )
    sensor_uuid = UUIDField(
        null=False,
        unique=True,
    )

    def serialize(self):
        srlz = super().serialize()
        slug = srlz.pop('slug')
        return {slug: srlz}

