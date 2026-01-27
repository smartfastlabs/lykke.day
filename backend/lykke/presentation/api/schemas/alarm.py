"""Alarm schema."""

from datetime import datetime as dt_datetime, time as dt_time
from uuid import UUID

from lykke.domain.value_objects.day import AlarmStatus, AlarmType

from .base import BaseSchema


class AlarmSchema(BaseSchema):
    """API schema for Alarm value object."""

    id: UUID | None = None
    name: str
    time: dt_time
    datetime: dt_datetime | None = None
    type: AlarmType
    url: str
    status: AlarmStatus = AlarmStatus.ACTIVE
    snoozed_until: dt_datetime | None = None


class AlarmPresetSchema(BaseSchema):
    """API schema for an alarm preset stored in user settings."""

    id: UUID | None = None
    name: str | None = None
    time: dt_time | None = None
    type: AlarmType = AlarmType.URL
    url: str = ""
