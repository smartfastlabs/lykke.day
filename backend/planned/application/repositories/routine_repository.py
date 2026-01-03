"""Protocol for RoutineRepository."""

from planned.application.repositories.base import SimpleReadRepositoryProtocol
from planned.domain.entities import RoutineEntity


class RoutineRepositoryProtocol(SimpleReadRepositoryProtocol[RoutineEntity]):
    """Protocol defining the interface for routine repositories."""
    pass

