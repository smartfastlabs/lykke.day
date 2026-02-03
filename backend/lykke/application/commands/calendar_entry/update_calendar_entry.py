"""Command to update a calendar entry."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import CalendarEntryRepositoryReadOnlyProtocol
from lykke.domain.entities import CalendarEntryEntity
from lykke.domain.events.calendar_entry_events import CalendarEntryUpdatedEvent
from lykke.domain.value_objects import CalendarEntryUpdateObject


@dataclass(frozen=True)
class UpdateCalendarEntryCommand(Command):
    """Command to update a calendar entry."""

    calendar_entry_id: UUID
    update_data: CalendarEntryUpdateObject


class UpdateCalendarEntryHandler(
    BaseCommandHandler[UpdateCalendarEntryCommand, CalendarEntryEntity]
):
    """Update an existing calendar entry."""

    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol

    async def handle(
        self, command: UpdateCalendarEntryCommand
    ) -> CalendarEntryEntity:
        """Update the specified calendar entry."""
        async with self.new_uow() as uow:
            entry = await self.calendar_entry_ro_repo.get(command.calendar_entry_id)
            entry = entry.apply_calendar_entry_update(command.update_data)
            return uow.add(entry)
