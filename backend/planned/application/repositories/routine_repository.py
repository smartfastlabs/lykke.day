"""Protocol for RoutineRepository."""

from planned.application.repositories.base import SimpleReadRepositoryProtocol
from planned.domain import entities


class RoutineRepositoryProtocol(SimpleReadRepositoryProtocol[entities.Routine]):
    """Protocol defining the interface for routine repositories."""
    pass

