from peewee import (
    AutoField,
    CharField,
    BlobField,
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
    password_hash = BlobField(null=False)
    salt = BlobField(null=False)
    is_admin = BooleanField(null=False, default=False)

    _do_not_serialize = [
        'password_hash',
        'salt',
    ]
