"""Command to detach a task definition from a routine definition."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import RoutineDefinitionRepositoryReadOnlyProtocol
from lykke.domain.entities import RoutineDefinitionEntity


@dataclass(frozen=True)
class RemoveRoutineDefinitionTaskCommand(Command):
    """Command to remove a routine definition task."""

    routine_definition_id: UUID
    routine_definition_task_id: UUID


class RemoveRoutineDefinitionTaskHandler(
    BaseCommandHandler[RemoveRoutineDefinitionTaskCommand, RoutineDefinitionEntity]
):
    """Detach a RoutineDefinitionTask from a routine definition."""

    routine_definition_ro_repo: RoutineDefinitionRepositoryReadOnlyProtocol

    async def handle(
        self, command: RemoveRoutineDefinitionTaskCommand
    ) -> RoutineDefinitionEntity:
        """Remove an attached task from the routine definition.

        Args:
            command: The command containing the routine definition ID and task ID to remove.

        Returns:
            The updated routine definition entity.
        """
        async with self.new_uow() as uow:
            routine_definition = await self.routine_definition_ro_repo.get(
                command.routine_definition_id
            )
            updated_routine_definition = routine_definition.remove_task(
                command.routine_definition_task_id
            )
            return uow.add(updated_routine_definition)
