"""Command to add a time block to a day template."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities.day_template import DayTemplateEntity


@dataclass(frozen=True)
class AddDayTemplateTimeBlockCommand(Command):
    """Command to add a time block to a day template."""

    day_template_id: UUID
    time_block: value_objects.DayTemplateTimeBlock


class AddDayTemplateTimeBlockHandler(BaseCommandHandler[AddDayTemplateTimeBlockCommand, DayTemplateEntity]):
    """Add a time block to a day template."""

    async def handle(self, command: AddDayTemplateTimeBlockCommand) -> DayTemplateEntity:
        """Add a time block to the day template.

        Args:
            command: The command containing the day template ID and time block to add.

        Returns:
            The updated day template entity.
        """
        async with self.new_uow() as uow:
            day_template = await uow.day_template_ro_repo.get(command.day_template_id)
            updated = day_template.add_time_block(command.time_block)
            return uow.add(updated)
