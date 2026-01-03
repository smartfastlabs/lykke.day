from dataclasses import dataclass

from .base import BaseConfigObject


@dataclass(kw_only=True)
class Person(BaseConfigObject):
    name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    relationship: str | None = None
