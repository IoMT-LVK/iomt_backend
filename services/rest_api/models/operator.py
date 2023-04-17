from peewee import (
    AutoField,
    CharField,
    FixedCharField,
    BooleanField,
)

from .base import BaseModel


class Operator(BaseModel):
    id = AutoField()
    
    login = CharField(
        null=False,
        index=True,
        unique=True,
        max_length=32,
    )
    password = FixedCharField(null=False, max_length=128)
    is_admin = BooleanField(null=False, default=False)

    _do_not_serialize = [
        'password',
    ]
