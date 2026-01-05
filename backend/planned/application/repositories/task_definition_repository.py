"""Protocol for TaskDefinitionRepository."""

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.domain import value_objects
from planned.infrastructure import data_objects


class TaskDefinitionRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[data_objects.TaskDefinition]):
    """Read-only protocol defining the interface for task definition repositories."""

    Query = value_objects.TaskDefinitionQuery


class TaskDefinitionRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[data_objects.TaskDefinition]):
    """Read-write protocol defining the interface for task definition repositories."""

    Query = value_objects.TaskDefinitionQuery

