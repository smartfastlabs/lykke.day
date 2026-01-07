"""Protocol for TaskDefinitionRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain import data_objects


class TaskDefinitionRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[data_objects.TaskDefinition]):
    """Read-only protocol defining the interface for task definition repositories."""

    Query = value_objects.TaskDefinitionQuery


class TaskDefinitionRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[data_objects.TaskDefinition]):
    """Read-write protocol defining the interface for task definition repositories."""

    Query = value_objects.TaskDefinitionQuery

