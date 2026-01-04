from dataclasses import dataclass, field, replace
from typing import Any, Self
from uuid import UUID, uuid4

from planned.domain.events.base import DomainEvent


@dataclass(kw_only=True)
class BaseObject:
    """Base class for all domain objects."""

    def clone(self, **kwargs: dict[str, Any]) -> Self:
        # Exclude init=False fields from replace() call
        # These fields cannot be specified in replace() but we don't want to include them anyway
        from dataclasses import fields

        init_false_fields = {f.name for f in fields(self) if not f.init}
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k not in init_false_fields
        }
        return replace(self, **filtered_kwargs)


@dataclass(kw_only=True)
class BaseEntityObject(BaseObject):
    """Base class for all domain entities (aggregate roots).

    All entities are aggregate roots and can raise domain events
    that are collected and dispatched after transaction commit.

    Subclasses should:
    1. Enforce business invariants
    2. Raise domain events when important things happen
    3. Only expose methods that maintain consistency
    """

    id: UUID = field(default_factory=uuid4)
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


@dataclass(kw_only=True)
class BaseConfigObject(BaseEntityObject):
    pass
