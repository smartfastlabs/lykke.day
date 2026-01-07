"""Protocol for RoutineRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import RoutineEntity


class RoutineRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[RoutineEntity]):
    """Read-only protocol defining the interface for routine repositories."""

    Query = value_objects.RoutineQuery


class RoutineRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[RoutineEntity]):
    """Read-write protocol defining the interface for routine repositories."""

    Query = value_objects.RoutineQuery

