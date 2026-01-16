"""Command to update a goal's status on a day."""

from datetime import date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


class UpdateGoalStatusHandler(BaseCommandHandler):
    """Updates a goal's status on a day."""

    async def update_goal_status(
        self, date: date, goal_id: UUID, status: value_objects.GoalStatus
    ) -> DayEntity:
        """Update a goal's status on a day.

        Args:
            date: The date of the day containing the goal
            goal_id: The ID of the goal to update
            status: The new status for the goal

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            # Update the goal status (this emits a domain event)
            day.update_goal_status(goal_id, status)

            # Add entity to UoW for saving
            uow.add(day)
            return day
