"""Command to delete a routine definition."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command


@dataclass(frozen=True)
class DeleteRoutineDefinitionCommand(Command):
    """Command to delete a routine definition."""

    routine_definition_id: UUID


class DeleteRoutineDefinitionHandler(
    BaseCommandHandler[DeleteRoutineDefinitionCommand, None]
):
    """Deletes a routine definition."""

    async def handle(self, command: DeleteRoutineDefinitionCommand) -> None:
        """Delete a routine definition.

        Args:
            command: The command containing the routine definition ID to delete.
        """
        async with self.new_uow() as uow:
            routine_definition = await uow.routine_definition_ro_repo.get(
                command.routine_definition_id
            )
            routine_definition.delete()
            uow.add(routine_definition)
