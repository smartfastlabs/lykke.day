"""Base classes for domain events and aggregate roots."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from ..entities.base import BaseEntityObject


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for all domain events.

    Domain events represent something important that happened in the domain.
    They are immutable and contain all the information needed to understand
    what happened.
    """

    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(kw_only=True)
class BaseAggregateRoot(BaseEntityObject):
    """Base class for aggregate roots with domain event support.

    Aggregate roots are the entry points to aggregates and are responsible
    for maintaining consistency boundaries. They can raise domain events
    that are collected and dispatched after transaction commit.

    Subclasses should:
    1. Enforce business invariants
    2. Raise domain events when important things happen
    3. Only expose methods that maintain consistency
    """

    _domain_events: list[DomainEvent] = field(init=False, default_factory=list)

    def _add_event(self, event: DomainEvent) -> None:
        """Add a domain event to be dispatched after commit.

        Args:
            event: The domain event to add.
        """
        self._domain_events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        """Collect and clear all domain events from this aggregate.

        Returns:
            A list of domain events that were raised.
        """
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def has_events(self) -> bool:
        """Check if this aggregate has any pending domain events.

        Returns:
            True if there are pending events, False otherwise.
        """
        return len(self._domain_events) > 0
