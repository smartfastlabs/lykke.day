"""Command to delete a factoid."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command


@dataclass(frozen=True)
class DeleteFactoidCommand(Command):
    """Command to delete a factoid."""

    factoid_id: UUID


class DeleteFactoidHandler(BaseCommandHandler[DeleteFactoidCommand, None]):
    """Deletes a factoid."""

    async def handle(self, command: DeleteFactoidCommand) -> None:
        """Delete a factoid.

        Args:
            command: The command containing the factoid ID to delete

        Raises:
            NotFoundError: If factoid not found
        """
        async with self.new_uow() as uow:
            factoid = await self.factoid_ro_repo.get(command.factoid_id)
            await uow.delete(factoid)
