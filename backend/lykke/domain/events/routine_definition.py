"""Domain events for RoutineDefinition aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from lykke.domain.events.base import EntityUpdatedEvent
from lykke.domain.value_objects.update import RoutineDefinitionUpdateObject


@dataclass(frozen=True, kw_only=True)
class RoutineDefinitionUpdatedEvent(
    EntityUpdatedEvent[RoutineDefinitionUpdateObject]
):
    """Event raised when a routine definition is updated via apply_update()."""
