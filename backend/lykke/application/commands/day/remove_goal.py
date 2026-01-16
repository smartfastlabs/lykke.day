"""Command to remove a goal from a day."""

from datetime import date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


class RemoveGoalHandler(BaseCommandHandler):
    """Removes a goal from a day."""

    async def remove_goal(self, date: date, goal_id: UUID) -> DayEntity:
        """Remove a goal from a day.

        Args:
            date: The date of the day containing the goal
            goal_id: The ID of the goal to remove

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            # Remove the goal (this emits a domain event)
            day.remove_goal(goal_id)

            # Add entity to UoW for saving
            uow.add(day)
            return day
