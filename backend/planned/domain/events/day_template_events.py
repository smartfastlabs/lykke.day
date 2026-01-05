"""Domain events related to DayTemplate aggregates."""

from dataclasses import dataclass

from planned.domain.entities.day_template import DayTemplateEntity
from planned.domain.value_objects.update import DayTemplateUpdateObject

from .base import DomainEvent, EntityUpdatedEvent


@dataclass(frozen=True, kw_only=True)
class DayTemplateUpdatedEvent(EntityUpdatedEvent[DayTemplateUpdateObject, DayTemplateEntity]):
    """Event raised when a day template is updated via apply_update()."""

    pass

