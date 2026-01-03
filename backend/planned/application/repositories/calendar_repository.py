"""Protocol for CalendarRepository."""

from planned.application.repositories.base import (
    CrudRepositoryProtocol,
    ReadOnlyCrudRepositoryProtocol,
)
from planned.domain.entities import CalendarEntity


class CalendarRepositoryReadOnlyProtocol(ReadOnlyCrudRepositoryProtocol[CalendarEntity]):
    """Read-only protocol defining the interface for calendar repositories."""
    pass


class CalendarRepositoryReadWriteProtocol(CrudRepositoryProtocol[CalendarEntity]):
    """Read-write protocol defining the interface for calendar repositories."""
    pass

