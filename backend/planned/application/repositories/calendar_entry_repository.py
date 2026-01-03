"""Protocol for CalendarEntryRepository."""

from planned.application.repositories.base import (
    DateScopedCrudRepositoryProtocol,
    ReadOnlyDateScopedRepositoryProtocol,
)
from planned.domain.entities import CalendarEntryEntity


class CalendarEntryRepositoryReadOnlyProtocol(ReadOnlyDateScopedRepositoryProtocol[CalendarEntryEntity]):
    """Read-only protocol defining the interface for calendar entry repositories."""
    pass


class CalendarEntryRepositoryReadWriteProtocol(DateScopedCrudRepositoryProtocol[CalendarEntryEntity]):
    """Read-write protocol defining the interface for calendar entry repositories."""
    pass

