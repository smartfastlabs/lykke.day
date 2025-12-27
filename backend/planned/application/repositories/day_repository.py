"""Protocol for DayRepository."""

from typing import Protocol

from planned.domain.entities import Day
from planned.infrastructure.repositories.base.repository import ChangeHandler


class DayRepositoryProtocol(Protocol):
    """Protocol defining the interface for day repositories."""

    async def get(self, key: str) -> Day:
        """Get a day by key (date string)."""
        ...

    async def put(self, obj: Day) -> Day:
        """Save or update a day."""
        ...

    def listen(self, handler: ChangeHandler[Day]) -> None:
        """Register a change handler for day events."""
        ...

