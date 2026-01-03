"""Protocol for RoutineRepository."""

from planned.application.repositories.base import SimpleReadRepositoryProtocol
from planned.domain.entities import RoutineEntity


class RoutineRepositoryReadOnlyProtocol(SimpleReadRepositoryProtocol[RoutineEntity]):
    """Read-only protocol defining the interface for routine repositories."""
    pass


class RoutineRepositoryReadWriteProtocol(SimpleReadRepositoryProtocol[RoutineEntity]):
    """Read-write protocol defining the interface for routine repositories."""
    pass

