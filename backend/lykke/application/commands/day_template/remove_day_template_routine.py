"""Command to detach a routine definition from a day template."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities.day_template import DayTemplateEntity


@dataclass(frozen=True)
class RemoveDayTemplateRoutineDefinitionCommand(Command):
    """Command to remove a routine definition from a day template."""

    day_template_id: UUID
    routine_definition_id: UUID


class RemoveDayTemplateRoutineDefinitionHandler(
    BaseCommandHandler[RemoveDayTemplateRoutineDefinitionCommand, DayTemplateEntity]
):
    """Detach a routine definition from a day template."""

    async def handle(
        self, command: RemoveDayTemplateRoutineDefinitionCommand
    ) -> DayTemplateEntity:
        """Remove an attached routine definition from the day template.

        Args:
            command: The command containing the day template ID and routine definition ID to detach.

        Returns:
            The updated day template entity.
        """
        async with self.new_uow() as uow:
            day_template = await uow.day_template_ro_repo.get(command.day_template_id)
            updated_day_template = day_template.remove_routine_definition(
                command.routine_definition_id
            )
            return uow.add(updated_day_template)
