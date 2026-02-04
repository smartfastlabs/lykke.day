"""Command to delete a tactic."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import TacticRepositoryReadOnlyProtocol
from lykke.domain.entities import TacticEntity


@dataclass(frozen=True)
class DeleteTacticCommand(Command):
    """Command to delete a tactic."""

    tactic_id: UUID


class DeleteTacticHandler(BaseCommandHandler[DeleteTacticCommand, None]):
    """Deletes a tactic."""

    tactic_ro_repo: TacticRepositoryReadOnlyProtocol

    async def handle(self, command: DeleteTacticCommand) -> None:
        """Delete a tactic."""
        async with self.new_uow() as uow:
            tactic = await self.tactic_ro_repo.get(command.tactic_id)
            await uow.delete(tactic)
