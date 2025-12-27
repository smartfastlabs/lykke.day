"""Protocol for TaskRepository."""

import datetime
from collections.abc import Callable
from typing import Protocol

from planned.domain.entities import Task
from planned.infrastructure.repositories.base.repository import ChangeHandler


class TaskRepositoryProtocol(Protocol):
    """Protocol defining the interface for task repositories."""

    async def get(self, date: datetime.date, key: str) -> Task:
        """Get a task by date and key."""
        ...

    async def put(self, obj: Task) -> Task:
        """Save or update a task."""
        ...

    async def search(self, date: datetime.date) -> list[Task]:
        """Search for tasks on a specific date."""
        ...

    async def delete(self, obj: Task) -> None:
        """Delete a task."""
        ...

    async def delete_by_date(
        self,
        date: datetime.date | str,
        filter_by: Callable[[Task], bool] | None = None,
    ) -> None:
        """Delete tasks by date, optionally filtered."""
        ...

    def listen(self, handler: ChangeHandler[Task]) -> None:
        """Register a change handler for task events."""
        ...

