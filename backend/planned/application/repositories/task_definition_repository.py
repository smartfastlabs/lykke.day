"""Protocol for TaskDefinitionRepository."""

from typing import Protocol

from planned.domain.entities import TaskDefinition


class TaskDefinitionRepositoryProtocol(Protocol):
    """Protocol defining the interface for task definition repositories."""

    async def get(self, key: str) -> TaskDefinition:
        """Get a task definition by key."""
        ...

    async def all(self) -> list[TaskDefinition]:
        """Get all task definitions."""
        ...

