"""Protocol for DayTemplateRepository."""

from typing import Protocol

from planned.domain.entities import DayTemplate


class DayTemplateRepositoryProtocol(Protocol):
    """Protocol defining the interface for day template repositories."""

    async def get(self, key: str) -> DayTemplate:
        """Get a day template by key."""
        ...

    async def all(self) -> list[DayTemplate]:
        """Get all day templates."""
        ...

