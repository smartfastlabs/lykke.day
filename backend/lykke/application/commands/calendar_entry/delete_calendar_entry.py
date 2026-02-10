"""Command to delete a calendar entry."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import CalendarEntryRepositoryReadOnlyProtocol


@dataclass(frozen=True)
class DeleteCalendarEntryCommand(Command):
    """Command to delete a calendar entry."""

    calendar_entry_id: UUID


class DeleteCalendarEntryHandler(
    BaseCommandHandler[DeleteCalendarEntryCommand, None]
):
    """Delete a calendar entry (any platform; user-scoped)."""

    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol

    async def handle(self, command: DeleteCalendarEntryCommand) -> None:
        """Delete the specified calendar entry."""
        async with self.new_uow() as uow:
            entry = await self.calendar_entry_ro_repo.get(
                command.calendar_entry_id
            )
            await uow.delete(entry)
