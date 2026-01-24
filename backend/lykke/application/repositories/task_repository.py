"""Protocol for TaskRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import TaskEntity


class TaskRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[TaskEntity]):
    """Read-only protocol defining the interface for task repositories."""

    Query = value_objects.TaskQuery


class TaskRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[TaskEntity]):
    """Read-write protocol defining the interface for task repositories."""

    Query = value_objects.TaskQuery
