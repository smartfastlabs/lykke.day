"""Command to save a day to the database."""

from planned.application.commands.base import BaseCommandHandler
from planned.domain.entities import DayEntity


class SaveDayHandler(BaseCommandHandler):
    """Saves a day to the database."""

    async def save_day(self, day: DayEntity) -> DayEntity:
        """Save a day to the database.

        Args:
            day: The day entity to save

        Returns:
            The saved Day entity
        """
        async with self.new_uow() as uow:
            uow.add(day)
            return day
