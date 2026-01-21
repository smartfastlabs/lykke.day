"""Reminder schema."""

from datetime import datetime
from uuid import UUID

from lykke.domain.value_objects.day import ReminderStatus

from .base import BaseEntitySchema


class ReminderSchema(BaseEntitySchema):
    """API schema for Reminder value object."""

    name: str
    status: ReminderStatus
    created_at: datetime | None = None
