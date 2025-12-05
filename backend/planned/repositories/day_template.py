from planned.objects import DayTemplate

from .base import BaseConfigRepository


class DayTemplateRepository(BaseConfigRepository[DayTemplate]):
    Object = DayTemplate
    _prefix = "config/day-templates"
