"""Protocol for CalendarRepository."""

from planned.application.repositories.base import CrudRepositoryProtocol
from planned.domain import entities


class CalendarRepositoryProtocol(CrudRepositoryProtocol[entities.Calendar]):
    """Protocol defining the interface for calendar repositories."""
    pass

