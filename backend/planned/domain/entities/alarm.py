from dataclasses import dataclass
from datetime import time as dt_time


from .. import value_objects
from .base import BaseConfigObject


@dataclass(kw_only=True)
class Alarm(BaseConfigObject):
    name: str
    time: dt_time
    type: value_objects.AlarmType
    description: str | None = None
    triggered_at: dt_time | None = None
