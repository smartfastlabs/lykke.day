"""Command to add a time block to a day template."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain import value_objects
from lykke.domain.entities.day_template import DayTemplateEntity


class AddDayTemplateTimeBlockHandler(BaseCommandHandler):
    """Add a time block to a day template."""

    async def run(
        self,
        day_template_id: UUID,
        time_block: value_objects.DayTemplateTimeBlock,
    ) -> DayTemplateEntity:
        """Add a time block to the day template.

        Args:
            day_template_id: ID of the day template to update.
            time_block: Time block to add.

        Returns:
            The updated day template entity.
        """
        async with self.new_uow() as uow:
            day_template = await uow.day_template_ro_repo.get(day_template_id)
            updated = day_template.add_time_block(time_block)
            uow.add(updated)
            return updated
