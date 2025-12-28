"""Protocol for CalendarRepository."""

from planned.application.repositories.base import CrudRepositoryProtocol
from planned.domain.entities import Calendar


class CalendarRepositoryProtocol(CrudRepositoryProtocol[Calendar]):
    """Protocol defining the interface for calendar repositories."""
    pass

