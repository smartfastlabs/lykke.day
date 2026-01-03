"""Alarm schema."""

from datetime import time as dt_time
from uuid import UUID

from planned.domain.value_objects.alarm import AlarmType

from .base import BaseEntitySchema


class Alarm(BaseEntitySchema):
    """API schema for Alarm entity."""

    name: str
    time: dt_time
    type: AlarmType
    description: str | None = None
    triggered_at: dt_time | None = None

