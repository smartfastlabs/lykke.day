"""Protocol for RoutineDefinitionRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import RoutineDefinitionEntity


class RoutineDefinitionRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[RoutineDefinitionEntity]
):
    """Read-only protocol defining the interface for routine definition repositories."""

    Query = value_objects.RoutineDefinitionQuery


class RoutineDefinitionRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[RoutineDefinitionEntity]
):
    """Read-write protocol defining the interface for routine definition repositories."""

    Query = value_objects.RoutineDefinitionQuery
