"""Command to add a goal to a day."""

from datetime import date

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain.entities import DayEntity


class AddGoalToDayHandler(BaseCommandHandler):
    """Adds a goal to a day."""

    async def add_goal(self, date: date, name: str) -> DayEntity:
        """Add a goal to a day.

        Args:
            date: The date of the day to add the goal to
            name: The name of the goal to add

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            # Add the goal (this emits a domain event)
            day.add_goal(name)

            # Add entity to UoW for saving
            uow.add(day)
            return day
