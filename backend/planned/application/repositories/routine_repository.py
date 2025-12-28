"""Protocol for RoutineRepository."""

from planned.application.repositories.base import SimpleReadRepositoryProtocol
from planned.domain.entities import Routine


class RoutineRepositoryProtocol(SimpleReadRepositoryProtocol[Routine]):
    """Protocol defining the interface for routine repositories."""
    pass

