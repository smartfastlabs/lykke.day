"""Command to delete a tactic."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import TacticEntity


@dataclass(frozen=True)
class DeleteTacticCommand(Command):
    """Command to delete a tactic."""

    tactic_id: UUID


class DeleteTacticHandler(BaseCommandHandler[DeleteTacticCommand, None]):
    """Deletes a tactic."""

    async def handle(self, command: DeleteTacticCommand) -> None:
        """Delete a tactic."""
        async with self.new_uow() as uow:
            tactic = await uow.tactic_ro_repo.get(command.tactic_id)
            await uow.delete(tactic)
