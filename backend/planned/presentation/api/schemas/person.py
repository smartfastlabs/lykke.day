"""Person schema."""

from uuid import UUID

from .base import BaseEntitySchema


class Person(BaseEntitySchema):
    """API schema for Person entity."""

    name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    relationship: str | None = None

