"""Protocol for DayRepository."""

from planned.application.repositories.base import SimpleDateScopedRepositoryProtocol
from planned.domain import entities


class DayRepositoryProtocol(SimpleDateScopedRepositoryProtocol[entities.Day]):
    """Protocol defining the interface for day repositories."""
    pass

