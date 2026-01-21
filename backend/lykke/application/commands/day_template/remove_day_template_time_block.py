"""Command to remove a time block from a day template."""

from dataclasses import dataclass
from datetime import time
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities.day_template import DayTemplateEntity


@dataclass(frozen=True)
class RemoveDayTemplateTimeBlockCommand(Command):
    """Command to remove a time block from a day template."""

    day_template_id: UUID
    time_block_definition_id: UUID
    start_time: time


class RemoveDayTemplateTimeBlockHandler(BaseCommandHandler[RemoveDayTemplateTimeBlockCommand, DayTemplateEntity]):
    """Remove a time block from a day template."""

    async def handle(self, command: RemoveDayTemplateTimeBlockCommand) -> DayTemplateEntity:
        """Remove a time block from the day template.

        Args:
            command: The command containing the day template ID, time block definition ID, and start time.

        Returns:
            The updated day template entity.
        """
        async with self.new_uow() as uow:
            day_template = await uow.day_template_ro_repo.get(command.day_template_id)
            updated = day_template.remove_time_block(
                command.time_block_definition_id, command.start_time
            )
            return uow.add(updated)
