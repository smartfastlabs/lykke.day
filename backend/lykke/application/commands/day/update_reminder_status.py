"""Command to update a reminder's status on a day."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class UpdateReminderStatusCommand(Command):
    """Command to update a reminder's status on a day."""

    date: date
    reminder_id: UUID
    status: value_objects.ReminderStatus


class UpdateReminderStatusHandler(
    BaseCommandHandler[UpdateReminderStatusCommand, DayEntity]
):
    """Updates a reminder's status on a day."""

    async def handle(self, command: UpdateReminderStatusCommand) -> DayEntity:
        """Update a reminder's status on a day.

        Args:
            command: The command containing the date, reminder ID, and status

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            # Update the reminder status (this emits a domain event if status changed)
            day.update_reminder_status(command.reminder_id, command.status)

            # Only add entity to UoW if it was actually modified (has events)
            # If status didn't change, update_reminder_status returns early without events
            if day.has_events():
                uow.add(day)
            return day
