"""Command to update a goal's status on a day."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class UpdateGoalStatusCommand(Command):
    """Command to update a goal's status on a day."""

    date: date
    goal_id: UUID
    completed: bool


class UpdateGoalStatusHandler(BaseCommandHandler[UpdateGoalStatusCommand, DayEntity]):
    """Updates a goal's status on a day."""

    async def handle(self, command: UpdateGoalStatusCommand) -> DayEntity:
        """Update a goal's status on a day.

        Args:
            command: The command containing the date, goal ID, and completion status

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            # Update the goal status (this emits a domain event if status changed)
            status = value_objects.GoalStatus.COMPLETE if command.completed else value_objects.GoalStatus.INCOMPLETE
            day.update_goal_status(command.goal_id, status)

            # Only add entity to UoW if it was actually modified (has events)
            # If status didn't change, update_goal_status returns early without events
            if day.has_events():
                uow.add(day)
            return day
