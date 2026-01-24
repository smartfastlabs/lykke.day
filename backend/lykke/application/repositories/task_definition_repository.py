"""Protocol for TaskDefinitionRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import TaskDefinitionEntity


class TaskDefinitionRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[TaskDefinitionEntity]
):
    """Read-only protocol defining the interface for task definition repositories."""

    Query = value_objects.TaskDefinitionQuery


class TaskDefinitionRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[TaskDefinitionEntity]
):
    """Read-write protocol defining the interface for task definition repositories."""

    Query = value_objects.TaskDefinitionQuery
