"""Command to create a new day template."""

from planned.application.commands.base import BaseCommandHandler
from planned.domain import data_objects


class CreateDayTemplateHandler(BaseCommandHandler):
    """Creates a new day template."""

    async def run(
        self, day_template: data_objects.DayTemplate
    ) -> data_objects.DayTemplate:
        """Create a new day template.

        Args:
            day_template: The day template data object to create

        Returns:
            The created day template data object
        """
        async with self.new_uow() as uow:
            await uow.create(day_template)
            return day_template
