"""Command to create a new day template."""

from planned.application.commands.base import BaseCommandHandler
from planned.domain.entities.day_template import DayTemplateEntity


class CreateDayTemplateHandler(BaseCommandHandler):
    """Creates a new day template."""

    async def run(
        self, day_template: DayTemplateEntity
    ) -> DayTemplateEntity:
        """Create a new day template.

        Args:
            day_template: The day template entity to create

        Returns:
            The created day template entity
        """
        async with self.new_uow() as uow:
            await uow.create(day_template)
            return day_template
