"""Protocol for CalendarEntrySeriesRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntrySeriesEntity


class CalendarEntrySeriesRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[CalendarEntrySeriesEntity]
):
    """Read-only protocol for calendar entry series repositories."""

    Query = value_objects.CalendarEntrySeriesQuery


class CalendarEntrySeriesRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[CalendarEntrySeriesEntity]
):
    """Read-write protocol for calendar entry series repositories."""

    Query = value_objects.CalendarEntrySeriesQuery

