"""Protocol for CalendarEntryRepository."""

from planned.application.repositories.base import DateScopedCrudRepositoryProtocol
from planned.domain.entities import CalendarEntry


class CalendarEntryRepositoryProtocol(DateScopedCrudRepositoryProtocol[CalendarEntry]):
    """Protocol defining the interface for calendar entry repositories."""
    pass

