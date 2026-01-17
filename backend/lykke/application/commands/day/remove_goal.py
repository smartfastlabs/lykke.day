"""Command to remove a goal from a day."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class RemoveGoalCommand(Command):
    """Command to remove a goal from a day."""

    date: date
    goal_id: UUID


class RemoveGoalHandler(BaseCommandHandler[RemoveGoalCommand, DayEntity]):
    """Removes a goal from a day."""

    async def handle(self, command: RemoveGoalCommand) -> DayEntity:
        """Remove a goal from a day.

        Args:
            command: The command containing the date and goal ID

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            # Remove the goal (this emits a domain event)
            day.remove_goal(command.goal_id)

            # Add entity to UoW for saving
            uow.add(day)
            return day
