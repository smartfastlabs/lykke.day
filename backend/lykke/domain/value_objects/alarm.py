from dataclasses import dataclass
from datetime import time as dt_time
from enum import Enum

from .base import BaseValueObject


class AlarmType(str, Enum):
    GENTLE = "GENTLE"
    FIRM = "FIRM"
    LOUD = "LOUD"
    SIREN = "SIREN"


@dataclass(kw_only=True)
class Alarm(BaseValueObject):
    """Alarm value object for Days and DayTemplates."""
    
    name: str
    time: dt_time
    type: AlarmType
    description: str | None = None
    triggered_at: dt_time | None = None

