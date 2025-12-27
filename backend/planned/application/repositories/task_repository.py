"""Protocol for TaskRepository."""

import datetime
from collections.abc import Callable

from planned.application.repositories.base import DateScopedCrudRepositoryProtocol
from planned.domain.entities import Task


class TaskRepositoryProtocol(DateScopedCrudRepositoryProtocol[Task]):
    """Protocol defining the interface for task repositories."""

    async def delete_by_date(
        self,
        date: datetime.date | str,
        filter_by: Callable[[Task], bool] | None = None,
    ) -> None:
        """Delete tasks by date, optionally filtered."""
        ...

