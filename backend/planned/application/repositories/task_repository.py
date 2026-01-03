"""Protocol for TaskRepository."""

from planned.application.repositories.base import DateScopedCrudRepositoryProtocol
from planned.domain.entities import TaskEntity


class TaskRepositoryProtocol(DateScopedCrudRepositoryProtocol[TaskEntity]):
    """Protocol defining the interface for task repositories."""
    pass

