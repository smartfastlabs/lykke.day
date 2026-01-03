"""Protocol for TaskDefinitionRepository."""

from planned.application.repositories.base import (
    CrudRepositoryProtocol,
    ReadOnlyCrudRepositoryProtocol,
)
from planned.domain.entities import TaskDefinitionEntity


class TaskDefinitionRepositoryReadOnlyProtocol(ReadOnlyCrudRepositoryProtocol[TaskDefinitionEntity]):
    """Read-only protocol defining the interface for task definition repositories."""
    pass


class TaskDefinitionRepositoryReadWriteProtocol(CrudRepositoryProtocol[TaskDefinitionEntity]):
    """Read-write protocol defining the interface for task definition repositories."""
    pass

