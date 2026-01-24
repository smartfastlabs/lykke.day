"""Command to attach a routine definition to a day template."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities.day_template import DayTemplateEntity


@dataclass(frozen=True)
class AddDayTemplateRoutineDefinitionCommand(Command):
    """Command to add a routine definition to a day template."""

    day_template_id: UUID
    routine_definition_id: UUID


class AddDayTemplateRoutineDefinitionHandler(
    BaseCommandHandler[AddDayTemplateRoutineDefinitionCommand, DayTemplateEntity]
):
    """Attach a routine definition to a day template."""

    async def handle(
        self, command: AddDayTemplateRoutineDefinitionCommand
    ) -> DayTemplateEntity:
        """Attach a routine definition to the day template.

        Args:
            command: The command containing the day template ID and routine definition ID to attach.

        Returns:
            The updated day template entity.
        """
        async with self.new_uow() as uow:
            day_template = await uow.day_template_ro_repo.get(command.day_template_id)
            updated = day_template.add_routine_definition(
                command.routine_definition_id
            )
            return uow.add(updated)
