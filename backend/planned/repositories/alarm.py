from planned.objects.alarm import Alarm

from .base import BaseRepository


class AlarmRepository(BaseRepository[Alarm]):
    Object = Alarm
    _prefix = "config/alarms"
