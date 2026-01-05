"""Command to create a new calendar."""

from planned.application.commands.base import BaseCommandHandler
from planned.domain.entities import CalendarEntity


class CreateCalendarHandler(BaseCommandHandler):
    """Creates a new calendar."""

    async def run(self, calendar: CalendarEntity) -> CalendarEntity:
        """Create a new calendar.

        Args:
            calendar: The calendar entity to create

        Returns:
            The created calendar entity
        """
        async with self.new_uow() as uow:
            await uow.create(calendar)
            return calendar
