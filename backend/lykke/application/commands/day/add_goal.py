"""Command to add a goal to a day."""

from dataclasses import dataclass
from datetime import date

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class AddGoalToDayCommand(Command):
    """Command to add a goal to a day."""

    date: date
    goal: str


class AddGoalToDayHandler(BaseCommandHandler[AddGoalToDayCommand, DayEntity]):
    """Adds a goal to a day."""

    async def handle(self, command: AddGoalToDayCommand) -> DayEntity:
        """Add a goal to a day.

        Args:
            command: The command containing the date and goal name

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            # Add the goal (this emits a domain event)
            day.add_goal(command.goal)

            # Add entity to UoW for saving
            uow.add(day)
            return day
