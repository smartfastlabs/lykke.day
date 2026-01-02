"""Protocol for TaskRepository."""

from planned.application.repositories.base import DateScopedCrudRepositoryProtocol
from planned.domain import entities


class TaskRepositoryProtocol(DateScopedCrudRepositoryProtocol[entities.Task]):
    """Protocol defining the interface for task repositories."""
    pass

