"""Protocol for TaskRepository."""

from planned.application.repositories.base import (
    DateScopedCrudRepositoryProtocol,
    ReadOnlyDateScopedRepositoryProtocol,
)
from planned.domain.entities import TaskEntity


class TaskRepositoryReadOnlyProtocol(ReadOnlyDateScopedRepositoryProtocol[TaskEntity]):
    """Read-only protocol defining the interface for task repositories."""
    pass


class TaskRepositoryReadWriteProtocol(DateScopedCrudRepositoryProtocol[TaskEntity]):
    """Read-write protocol defining the interface for task repositories."""
    pass

