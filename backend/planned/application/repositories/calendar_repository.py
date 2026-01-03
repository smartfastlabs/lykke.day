"""Protocol for CalendarRepository."""

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.domain.entities import CalendarEntity


class CalendarRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[CalendarEntity]):
    """Read-only protocol defining the interface for calendar repositories."""


class CalendarRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[CalendarEntity]):
    """Read-write protocol defining the interface for calendar repositories."""

