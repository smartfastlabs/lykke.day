from datetime import time as dt_time


from ..value_objects.alarm import AlarmType
from .base import BaseConfigObject


class Alarm(BaseConfigObject):
    name: str
    time: dt_time
    type: AlarmType
    description: str | None = None
    triggered_at: dt_time | None = None
