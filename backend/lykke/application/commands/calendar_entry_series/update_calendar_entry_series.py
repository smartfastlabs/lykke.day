"""Command to update a calendar entry series."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.application.repositories import (
    CalendarEntrySeriesRepositoryReadOnlyProtocol,
)
from lykke.domain.entities import CalendarEntrySeriesEntity
from lykke.domain.events.calendar_entry_series_events import (
    CalendarEntrySeriesUpdatedEvent,
)
from lykke.domain.value_objects import CalendarEntrySeriesUpdateObject


class UpdateCalendarEntrySeriesHandler(BaseCommandHandler):
    """Update an existing calendar entry series."""

    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol

    async def run(
        self,
        series_id: UUID,
        update_data: CalendarEntrySeriesUpdateObject,
    ) -> CalendarEntrySeriesEntity:
        """Update the specified calendar entry series."""
        async with self.new_uow() as uow:
            series = await uow.calendar_entry_series_ro_repo.get(series_id)
            series = series.apply_update(
                update_data, CalendarEntrySeriesUpdatedEvent
            )
            uow.add(series)
            return series


