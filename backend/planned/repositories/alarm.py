from planned.objects.alarm import Alarm

from .base import BaseConfigRepository


class AlarmRepository(BaseConfigRepository[Alarm]):
    Object = Alarm
    _prefix = "config/alarms"
