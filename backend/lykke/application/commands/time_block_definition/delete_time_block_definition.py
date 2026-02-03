"""Command to delete a time block definition."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import TimeBlockDefinitionRepositoryReadOnlyProtocol


@dataclass(frozen=True)
class DeleteTimeBlockDefinitionCommand(Command):
    """Command to delete a time block definition."""

    time_block_definition_id: UUID


class DeleteTimeBlockDefinitionHandler(
    BaseCommandHandler[DeleteTimeBlockDefinitionCommand, None]
):
    """Deletes a time block definition."""

    time_block_definition_ro_repo: TimeBlockDefinitionRepositoryReadOnlyProtocol

    async def handle(self, command: DeleteTimeBlockDefinitionCommand) -> None:
        """Delete a time block definition.

        Args:
            command: The command containing the time block definition ID to delete.
        """
        async with self.new_uow() as uow:
            time_block_definition = await self.time_block_definition_ro_repo.get(
                command.time_block_definition_id
            )
            await uow.delete(time_block_definition)
