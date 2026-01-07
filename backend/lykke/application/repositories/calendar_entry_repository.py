"""Protocol for CalendarEntryRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity


class CalendarEntryRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[CalendarEntryEntity]
):
    """Read-only protocol defining the interface for calendar entry repositories."""

    Query = value_objects.CalendarEntryQuery

    async def get_by_platform_id(self, platform_id: str) -> CalendarEntryEntity | None:
        """Fetch a calendar entry by external platform ID if it exists."""
        ...


class CalendarEntryRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[CalendarEntryEntity]
):
    """Read-write protocol defining the interface for calendar entry repositories."""

    Query = value_objects.CalendarEntryQuery
