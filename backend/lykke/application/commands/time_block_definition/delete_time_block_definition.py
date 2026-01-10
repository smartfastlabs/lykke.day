"""Command to delete a time block definition."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler


class DeleteTimeBlockDefinitionHandler(BaseCommandHandler):
    """Deletes a time block definition."""

    async def run(self, time_block_definition_id: UUID) -> None:
        """Delete a time block definition.

        Args:
            time_block_definition_id: The ID of the time block definition to delete.
        """
        async with self.new_uow() as uow:
            time_block_definition = await uow.time_block_definition_ro_repo.get(
                time_block_definition_id
            )
            await uow.delete(time_block_definition)

