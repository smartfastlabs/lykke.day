"""Command to attach a task definition to a routine definition."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import RoutineDefinitionEntity
from lykke.domain.value_objects import RoutineDefinitionTask


@dataclass(frozen=True)
class AddRoutineDefinitionTaskCommand(Command):
    """Command to add a routine definition task."""

    routine_definition_id: UUID
    routine_definition_task: RoutineDefinitionTask


class AddRoutineDefinitionTaskHandler(
    BaseCommandHandler[AddRoutineDefinitionTaskCommand, RoutineDefinitionEntity]
):
    """Attach a RoutineDefinitionTask to a routine definition."""

    async def handle(
        self, command: AddRoutineDefinitionTaskCommand
    ) -> RoutineDefinitionEntity:
        """Attach a task to the routine definition.

        Args:
            command: The command containing the routine definition ID and task to attach.

        Returns:
            The updated routine definition entity.
        """
        async with self.new_uow() as uow:
            routine_definition = await uow.routine_definition_ro_repo.get(
                command.routine_definition_id
            )
            updated = routine_definition.add_task(command.routine_definition_task)
            return uow.add(updated)
