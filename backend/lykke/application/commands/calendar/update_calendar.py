"""Command to update an existing calendar."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import CalendarRepositoryReadOnlyProtocol
from lykke.domain.entities import CalendarEntity
from lykke.domain.events.calendar_events import CalendarUpdatedEvent
from lykke.domain.value_objects import CalendarUpdateObject


@dataclass(frozen=True)
class UpdateCalendarCommand(Command):
    """Command to update an existing calendar."""

    calendar_id: UUID
    update_data: CalendarUpdateObject


class UpdateCalendarHandler(BaseCommandHandler[UpdateCalendarCommand, CalendarEntity]):
    """Updates an existing calendar."""

    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol

    async def handle(self, command: UpdateCalendarCommand) -> CalendarEntity:
        """Update an existing calendar.

        Args:
            command: The command containing the calendar ID and update data

        Returns:
            The updated calendar entity

        Raises:
            NotFoundError: If calendar not found
        """
        async with self.new_uow() as uow:
            # Get the existing calendar
            calendar = await uow.calendar_ro_repo.get(command.calendar_id)

            # Apply updates using domain method (adds EntityUpdatedEvent)
            calendar = calendar.apply_update(command.update_data, CalendarUpdatedEvent)

            # Add entity to UoW for saving
            uow.add(calendar)
            return calendar

