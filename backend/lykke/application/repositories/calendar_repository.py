"""Protocol for CalendarRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity


class CalendarRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[CalendarEntity]):
    """Read-only protocol defining the interface for calendar repositories."""

    Query = value_objects.CalendarQuery


class CalendarRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[CalendarEntity]):
    """Read-write protocol defining the interface for calendar repositories."""

    Query = value_objects.CalendarQuery

