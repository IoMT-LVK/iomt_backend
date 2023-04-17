from peewee import (
    AutoField,
    CharField,
    FixedCharField,
    IntegerField,
    DateField,
    ManyToManyField,
    BlobField,
)

from .base import BaseModel
from .operator import Operator


class User(BaseModel):
    login = CharField(
        null=False,
        index=True,
        unique=True,
        max_length=32,
    )
    password_hash = BlobField(null=False)
    salt = BlobField(null=False)

    weight = IntegerField(null=True)
    height = IntegerField(null=True)
    email = CharField(null=False, max_length=320)
    name = CharField(null=False, max_length=32)
    surname = CharField(null=False, max_length=32)
    patronymic = CharField(null=True, max_length=32)
    born = DateField(null=True)
    allowed = ManyToManyField(Operator, 'allowed_users')

    _do_not_serialize = [
        'password_hash',
        'salt',
    ]

    def serialize(self):
        srlz = super().serialize()
        srlz['allowed'] = [op.id for op in self.allowed]
        print(f"{srlz=}")
        return srlz
