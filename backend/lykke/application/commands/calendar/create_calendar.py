"""Command to create a new calendar."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import CalendarEntity


@dataclass(frozen=True)
class CreateCalendarCommand(Command):
    """Command to create a new calendar."""

    calendar: CalendarEntity


class CreateCalendarHandler(BaseCommandHandler[CreateCalendarCommand, CalendarEntity]):
    """Creates a new calendar."""

    async def handle(self, command: CreateCalendarCommand) -> CalendarEntity:
        """Create a new calendar.

        Args:
            command: The command containing the calendar entity to create

        Returns:
            The created calendar entity
        """
        async with self.new_uow() as uow:
            return await uow.create(command.calendar)
