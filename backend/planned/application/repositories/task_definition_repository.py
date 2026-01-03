"""Protocol for TaskDefinitionRepository."""

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.domain.entities import TaskDefinitionEntity


class TaskDefinitionRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[TaskDefinitionEntity]):
    """Read-only protocol defining the interface for task definition repositories."""


class TaskDefinitionRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[TaskDefinitionEntity]):
    """Read-write protocol defining the interface for task definition repositories."""

