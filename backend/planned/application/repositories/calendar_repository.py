"""Protocol for CalendarRepository."""

from typing import Protocol

from planned.domain.entities import Calendar


class CalendarRepositoryProtocol(Protocol):
    """Protocol defining the interface for calendar repositories."""

    async def get(self, key: str) -> Calendar:
        """Get a calendar by key."""
        ...

    async def put(self, obj: Calendar) -> Calendar:
        """Save or update a calendar."""
        ...

    async def all(self) -> list[Calendar]:
        """Get all calendars."""
        ...

