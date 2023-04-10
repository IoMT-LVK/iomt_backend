
from .base import BaseModel


class User(BaseModel):
    # id = IntegerField()

    def serialize(self):
        return {"TODO": "serialize"}
