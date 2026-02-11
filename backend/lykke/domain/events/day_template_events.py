"""Domain events related to DayTemplate aggregates."""

from __future__ import annotations

from dataclasses import dataclass

from lykke.domain.value_objects.update import DayTemplateUpdateObject

from .base import EntityUpdatedEvent


@dataclass(frozen=True, kw_only=True)
class DayTemplateUpdatedEvent(EntityUpdatedEvent[DayTemplateUpdateObject]):
    """Event raised when a day template is updated via apply_update()."""
