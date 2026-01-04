"""Protocol for TaskDefinitionRepository."""

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.domain import value_objects
from planned.domain.entities import TaskDefinitionEntity


class TaskDefinitionRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[TaskDefinitionEntity]):
    """Read-only protocol defining the interface for task definition repositories."""

    Query = value_objects.TaskDefinitionQuery


class TaskDefinitionRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[TaskDefinitionEntity]):
    """Read-write protocol defining the interface for task definition repositories."""

    Query = value_objects.TaskDefinitionQuery

