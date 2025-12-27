"""Protocol for RoutineRepository."""

from typing import Protocol

from planned.domain.entities import Routine


class RoutineRepositoryProtocol(Protocol):
    """Protocol defining the interface for routine repositories."""

    async def get(self, key: str) -> Routine:
        """Get a routine by key."""
        ...

    async def all(self) -> list[Routine]:
        """Get all routines."""
        ...

