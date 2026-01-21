"""Command to add a reminder to a day."""

from dataclasses import dataclass
from datetime import date

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class AddReminderToDayCommand(Command):
    """Command to add a reminder to a day."""

    date: date
    reminder: str


class AddReminderToDayHandler(BaseCommandHandler[AddReminderToDayCommand, DayEntity]):
    """Adds a reminder to a day."""

    async def handle(self, command: AddReminderToDayCommand) -> DayEntity:
        """Add a reminder to a day.

        Args:
            command: The command containing the date and reminder name

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            # Add the reminder (this emits a domain event)
            day.add_reminder(command.reminder)

            # Add entity to UoW for saving
            return uow.add(day)
