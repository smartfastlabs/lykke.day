"""Alarm schema."""

from datetime import datetime as dt_datetime
from datetime import time

from lykke.domain.value_objects.day import AlarmType

from .base import BaseSchema


class AlarmSchema(BaseSchema):
    """API schema for Alarm value object."""

    name: str
    time: time
    datetime: dt_datetime | None = None
    type: AlarmType
    url: str
