"""Command to update an attached routine definition task."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import RoutineDefinitionEntity
from lykke.domain.value_objects import RoutineDefinitionTask


@dataclass(frozen=True)
class UpdateRoutineDefinitionTaskCommand(Command):
    """Command to update a routine definition task."""

    routine_definition_id: UUID
    routine_definition_task_id: UUID
    routine_definition_task: RoutineDefinitionTask


class UpdateRoutineDefinitionTaskHandler(
    BaseCommandHandler[UpdateRoutineDefinitionTaskCommand, RoutineDefinitionEntity]
):
    """Update the metadata or schedule of an attached RoutineDefinitionTask."""

    async def handle(
        self, command: UpdateRoutineDefinitionTaskCommand
    ) -> RoutineDefinitionEntity:
        """Update an attached RoutineDefinitionTask.

        Args:
            command: The command containing the routine definition ID, task ID, and task updates.

        Returns:
            The updated routine definition entity.
        """
        async with self.new_uow() as uow:
            routine_definition = await uow.routine_definition_ro_repo.get(
                command.routine_definition_id
            )
            updated_routine_definition = routine_definition.update_task(
                command.routine_definition_task
            )
            return uow.add(updated_routine_definition)
