"""Protocol for DayRepository."""

from planned.application.repositories.base import SimpleDateScopedRepositoryProtocol
from planned.domain.entities import Day


class DayRepositoryProtocol(SimpleDateScopedRepositoryProtocol[Day]):
    """Protocol defining the interface for day repositories."""
    pass

