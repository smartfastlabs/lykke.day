"""Domain events related to Day aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as dt_date
from typing import TYPE_CHECKING
from uuid import UUID

from lykke.domain.value_objects.day import GoalStatus
from lykke.domain.value_objects.update import DayUpdateObject

from .base import DomainEvent, EntityUpdatedEvent

__all__ = [
    "DayCompletedEvent",
    "DayScheduledEvent",
    "DayUnscheduledEvent",
    "DayUpdatedEvent",
    "GoalAddedEvent",
    "GoalStatusChangedEvent",
    "GoalRemovedEvent",
]


@dataclass(frozen=True, kw_only=True)
class DayScheduledEvent(DomainEvent):
    """Event raised when a day is scheduled."""

    day_id: UUID
    date: dt_date
    template_id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class DayCompletedEvent(DomainEvent):
    """Event raised when a day is marked as complete."""

    day_id: UUID
    date: dt_date


@dataclass(frozen=True, kw_only=True)
class DayUnscheduledEvent(DomainEvent):
    """Event raised when a day is unscheduled."""

    day_id: UUID
    date: dt_date


@dataclass(frozen=True, kw_only=True)
class DayUpdatedEvent(EntityUpdatedEvent[DayUpdateObject]):
    """Event raised when a day is updated via apply_update()."""


@dataclass(frozen=True, kw_only=True)
class GoalAddedEvent(DomainEvent):
    """Event raised when a goal is added to a day."""

    day_id: UUID
    date: dt_date
    goal_id: UUID
    goal_name: str


@dataclass(frozen=True, kw_only=True)
class GoalStatusChangedEvent(DomainEvent):
    """Event raised when a goal status changes."""

    day_id: UUID
    date: dt_date
    goal_id: UUID
    old_status: GoalStatus
    new_status: GoalStatus
    goal_name: str


@dataclass(frozen=True, kw_only=True)
class GoalRemovedEvent(DomainEvent):
    """Event raised when a goal is removed from a day."""

    day_id: UUID
    date: dt_date
    goal_id: UUID
    goal_name: str
