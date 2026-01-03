"""Protocol for CalendarRepository."""

from planned.application.repositories.base import CrudRepositoryProtocol
from planned.domain.entities import CalendarEntity


class CalendarRepositoryProtocol(CrudRepositoryProtocol[CalendarEntity]):
    """Protocol defining the interface for calendar repositories."""
    pass

