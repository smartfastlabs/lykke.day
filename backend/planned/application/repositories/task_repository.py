"""Protocol for TaskRepository."""

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.domain import value_objects
from planned.domain.entities import TaskEntity


class TaskRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[TaskEntity]):
    """Read-only protocol defining the interface for task repositories."""

    Query = value_objects.TaskQuery


class TaskRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[TaskEntity]):
    """Read-write protocol defining the interface for task repositories."""

    Query = value_objects.TaskQuery

