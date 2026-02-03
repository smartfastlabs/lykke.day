"""Command to delete a calendar."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import CalendarRepositoryReadOnlyProtocol


@dataclass(frozen=True)
class DeleteCalendarCommand(Command):
    """Command to delete a calendar."""

    calendar_id: UUID


class DeleteCalendarHandler(BaseCommandHandler[DeleteCalendarCommand, None]):
    """Deletes a calendar."""

    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol

    async def handle(self, command: DeleteCalendarCommand) -> None:
        """Delete a calendar.

        Args:
            command: The command containing the calendar ID to delete

        Raises:
            NotFoundError: If calendar not found
        """
        async with self.new_uow() as uow:
            calendar = await self.calendar_ro_repo.get(command.calendar_id)
            await uow.delete(calendar)
