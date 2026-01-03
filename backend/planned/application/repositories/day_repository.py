"""Protocol for DayRepository."""

from planned.application.repositories.base import SimpleDateScopedRepositoryProtocol
from planned.domain.entities import DayEntity


class DayRepositoryProtocol(SimpleDateScopedRepositoryProtocol[DayEntity]):
    """Protocol defining the interface for day repositories."""
    pass

