"""Command to remove a time block from a day template."""

from datetime import time
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain.entities.day_template import DayTemplateEntity


class RemoveDayTemplateTimeBlockHandler(BaseCommandHandler):
    """Remove a time block from a day template."""

    async def run(
        self,
        day_template_id: UUID,
        time_block_definition_id: UUID,
        start_time: time,
    ) -> DayTemplateEntity:
        """Remove a time block from the day template.

        Args:
            day_template_id: ID of the day template to update.
            time_block_definition_id: ID of the time block definition.
            start_time: Start time of the time block to remove.

        Returns:
            The updated day template entity.
        """
        async with self.new_uow() as uow:
            day_template = await uow.day_template_ro_repo.get(day_template_id)
            updated = day_template.remove_time_block(
                time_block_definition_id, start_time
            )
            uow.add(updated)
            return updated
