"""
Эта модель специально не перечислена в __init__
потому что не является открытой и общедоступной
"""
from peewee import (
    AutoField,
    CharField,
    UUIDField,
)

from .base import BaseModel


class Characteristic(BaseModel):
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
    # возможно тут стоило бы использовать UUIDField
    # но на бэке ээто особо не нужно, а в ручках может вызвать
    # неожиданные проблемы сравнения со строкой
    service_uuid = CharField(
        null=False,
        unique=False,
    )
    characteristic_uuid = CharField(
        null=False,
        unique=False,
    )

    _do_not_serialize = [
        'id',
    ]

    def serialize(self):
        srlz = super().serialize()
        slug = srlz.pop('slug')
        return {slug: srlz}

