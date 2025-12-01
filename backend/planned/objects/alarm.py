from datetime import time as dt_time
from enum import Enum

from pydantic import computed_field

from planned.utils.strings import slugify

from .base import BaseObject


class AlarmType(str, Enum):
    GENTLE = "GENTLE"
    FIRM = "FIRM"
    LOUD = "LOUD"
    SIREN = "SIREN"


class Alarm(BaseObject):
    name: str
    time: dt_time
    type: AlarmType
    description: str | None = None
