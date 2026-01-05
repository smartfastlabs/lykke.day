"""Domain events related to DayTemplate aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from planned.domain.value_objects.update import DayTemplateUpdateObject

from .base import DomainEvent, EntityUpdatedEvent

if TYPE_CHECKING:
    from planned.domain.entities.day_template import DayTemplateEntity


@dataclass(frozen=True, kw_only=True)
class DayTemplateUpdatedEvent(EntityUpdatedEvent[DayTemplateUpdateObject, "DayTemplateEntity"]):
    """Event raised when a day template is updated via apply_update()."""

