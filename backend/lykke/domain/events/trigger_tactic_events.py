"""Domain events related to Trigger and Tactic aggregates."""

from dataclasses import dataclass

from lykke.domain.value_objects.update import (
    TacticUpdateObject,
    TriggerUpdateObject,
)

from .base import EntityUpdatedEvent

__all__ = [
    "TacticUpdatedEvent",
    "TriggerUpdatedEvent",
]


@dataclass(frozen=True, kw_only=True)
class TriggerUpdatedEvent(EntityUpdatedEvent[TriggerUpdateObject]):
    """Event raised when a trigger is updated via apply_update()."""


@dataclass(frozen=True, kw_only=True)
class TacticUpdatedEvent(EntityUpdatedEvent[TacticUpdateObject]):
    """Event raised when a tactic is updated via apply_update()."""
