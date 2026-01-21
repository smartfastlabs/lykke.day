"""Command to delete a task definition."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command


@dataclass(frozen=True)
class DeleteTaskDefinitionCommand(Command):
    """Command to delete a task definition."""

    task_definition_id: UUID


class DeleteTaskDefinitionHandler(BaseCommandHandler[DeleteTaskDefinitionCommand, None]):
    """Deletes a task definition."""

    async def handle(self, command: DeleteTaskDefinitionCommand) -> None:
        """Delete a task definition.

        Args:
            command: The command containing the task definition ID to delete

        Raises:
            NotFoundError: If task definition not found
        """
        async with self.new_uow() as uow:
            task_definition = await uow.task_definition_ro_repo.get(command.task_definition_id)
            await uow.delete(task_definition)

