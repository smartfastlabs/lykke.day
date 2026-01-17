"""Command to attach a routine to a day template."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities.day_template import DayTemplateEntity


@dataclass(frozen=True)
class AddDayTemplateRoutineCommand(Command):
    """Command to add a routine to a day template."""

    day_template_id: UUID
    routine_id: UUID


class AddDayTemplateRoutineHandler(BaseCommandHandler[AddDayTemplateRoutineCommand, DayTemplateEntity]):
    """Attach a routine to a day template."""

    async def handle(self, command: AddDayTemplateRoutineCommand) -> DayTemplateEntity:
        """Attach a routine to the day template.

        Args:
            command: The command containing the day template ID and routine ID to attach.

        Returns:
            The updated day template entity.
        """
        async with self.new_uow() as uow:
            day_template = await uow.day_template_ro_repo.get(command.day_template_id)
            updated = day_template.add_routine(command.routine_id)
            uow.add(updated)
            return updated

