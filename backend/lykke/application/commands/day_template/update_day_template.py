"""Command to update an existing day template."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.domain.events.day_template_events import DayTemplateUpdatedEvent
from lykke.domain.value_objects import DayTemplateUpdateObject


@dataclass(frozen=True)
class UpdateDayTemplateCommand(Command):
    """Command to update an existing day template."""

    day_template_id: UUID
    update_data: DayTemplateUpdateObject


class UpdateDayTemplateHandler(BaseCommandHandler[UpdateDayTemplateCommand, DayTemplateEntity]):
    """Updates an existing day template."""

    async def handle(self, command: UpdateDayTemplateCommand) -> DayTemplateEntity:
        """Update an existing day template.

        Args:
            command: The command containing the day template ID and update data

        Returns:
            The updated day template entity

        Raises:
            NotFoundError: If day template not found
        """
        async with self.new_uow() as uow:
            # Get the existing day template
            day_template = await uow.day_template_ro_repo.get(command.day_template_id)

            # Apply updates using domain method (adds EntityUpdatedEvent)
            day_template = day_template.apply_update(
                command.update_data, DayTemplateUpdatedEvent
            )

            # Add entity to UoW for saving
            uow.add(day_template)
            return day_template
