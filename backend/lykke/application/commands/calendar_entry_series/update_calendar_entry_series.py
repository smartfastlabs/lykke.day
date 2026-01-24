"""Command to update a calendar entry series."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import (
    CalendarEntrySeriesRepositoryReadOnlyProtocol,
)
from lykke.domain.entities import CalendarEntrySeriesEntity
from lykke.domain.events.calendar_entry_series_events import (
    CalendarEntrySeriesUpdatedEvent,
)
from lykke.domain.value_objects import CalendarEntrySeriesUpdateObject


@dataclass(frozen=True)
class UpdateCalendarEntrySeriesCommand(Command):
    """Command to update a calendar entry series."""

    calendar_entry_series_id: UUID
    update_data: CalendarEntrySeriesUpdateObject


class UpdateCalendarEntrySeriesHandler(
    BaseCommandHandler[UpdateCalendarEntrySeriesCommand, CalendarEntrySeriesEntity]
):
    """Update an existing calendar entry series."""

    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol

    async def handle(
        self, command: UpdateCalendarEntrySeriesCommand
    ) -> CalendarEntrySeriesEntity:
        """Update the specified calendar entry series."""
        async with self.new_uow() as uow:
            series = await uow.calendar_entry_series_ro_repo.get(
                command.calendar_entry_series_id
            )
            series = series.apply_update(
                command.update_data, CalendarEntrySeriesUpdatedEvent
            )
            return uow.add(series)
