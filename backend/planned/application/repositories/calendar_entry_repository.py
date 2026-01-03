"""Protocol for CalendarEntryRepository."""

from planned.application.repositories.base import DateScopedCrudRepositoryProtocol
from planned.domain.entities import CalendarEntity, CalendarEntryEntity


class CalendarEntryRepositoryProtocol(DateScopedCrudRepositoryProtocol[CalendarEntryEntity]):
    """Protocol defining the interface for calendar entry repositories."""
    pass

