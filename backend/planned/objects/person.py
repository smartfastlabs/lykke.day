from .base import BaseConfigObject


class Person(BaseConfigObject):
    name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    relationship: str | None = None
