from planned.domain.entities import DayTemplate

from .base import BaseConfigRepository
from .base.schema import day_templates


class DayTemplateRepository(BaseConfigRepository[DayTemplate]):
    Object = DayTemplate
    table = day_templates
