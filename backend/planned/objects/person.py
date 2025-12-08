from .base import BaseObject


class Person(BaseObject):
    name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    relationship: str | None = None
