"""Protocol for RoutineRepository."""

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.domain.entities import RoutineEntity


class RoutineRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[RoutineEntity]):
    """Read-only protocol defining the interface for routine repositories."""


class RoutineRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[RoutineEntity]):
    """Read-write protocol defining the interface for routine repositories."""

