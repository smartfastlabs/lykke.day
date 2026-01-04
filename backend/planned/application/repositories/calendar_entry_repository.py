"""Protocol for CalendarEntryRepository."""

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.domain import value_objects
from planned.domain.entities import CalendarEntryEntity


class CalendarEntryRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[CalendarEntryEntity]):
    """Read-only protocol defining the interface for calendar entry repositories."""

    Query = value_objects.CalendarEntryQuery


class CalendarEntryRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[CalendarEntryEntity]):
    """Read-write protocol defining the interface for calendar entry repositories."""

    Query = value_objects.CalendarEntryQuery

