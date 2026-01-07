"""Alarm schema."""

from datetime import time as dt_time

from pydantic import BaseModel

from lykke.domain.value_objects.alarm import AlarmType


class AlarmSchema(BaseModel):
    """API schema for Alarm value object."""

    name: str
    time: dt_time
    type: AlarmType
    description: str | None = None
    triggered_at: dt_time | None = None

