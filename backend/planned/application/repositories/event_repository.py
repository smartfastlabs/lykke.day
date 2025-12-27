"""Protocol for EventRepository."""

import datetime
from typing import Protocol

from planned.domain.entities import Event
from planned.infrastructure.repositories.base.repository import ChangeHandler


class EventRepositoryProtocol(Protocol):
    """Protocol defining the interface for event repositories."""

    async def get(self, date: datetime.date, key: str) -> Event:
        """Get an event by date and key."""
        ...

    async def put(self, obj: Event) -> Event:
        """Save or update an event."""
        ...

    async def search(self, date: datetime.date) -> list[Event]:
        """Search for events on a specific date."""
        ...

    async def delete(self, obj: Event) -> None:
        """Delete an event."""
        ...

    def listen(self, handler: ChangeHandler[Event]) -> None:
        """Register a change handler for event events."""
        ...

