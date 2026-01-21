"""Domain events related to TimeBlockDefinition aggregates."""

from __future__ import annotations

from dataclasses import dataclass

from lykke.domain.value_objects.update import TimeBlockDefinitionUpdateObject

from .base import EntityUpdatedEvent

__all__ = [
    "TimeBlockDefinitionUpdatedEvent",
]


@dataclass(frozen=True, kw_only=True)
class TimeBlockDefinitionUpdatedEvent(
    EntityUpdatedEvent[TimeBlockDefinitionUpdateObject]
):
    """Event raised when a time block definition is updated via apply_update()."""

