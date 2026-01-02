"""Protocol for CalendarEntryRepository."""

from planned.application.repositories.base import DateScopedCrudRepositoryProtocol
from planned.domain import entities


class CalendarEntryRepositoryProtocol(DateScopedCrudRepositoryProtocol[entities.CalendarEntry]):
    """Protocol defining the interface for calendar entry repositories."""
    pass

