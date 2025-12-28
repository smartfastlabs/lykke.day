"""Protocol for TaskRepository."""

from planned.application.repositories.base import DateScopedCrudRepositoryProtocol
from planned.domain.entities import Task


class TaskRepositoryProtocol(DateScopedCrudRepositoryProtocol[Task]):
    """Protocol defining the interface for task repositories."""
    pass

