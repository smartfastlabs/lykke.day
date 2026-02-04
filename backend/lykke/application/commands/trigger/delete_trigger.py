"""Command to delete a trigger."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import TriggerRepositoryReadOnlyProtocol


@dataclass(frozen=True)
class DeleteTriggerCommand(Command):
    """Command to delete a trigger."""

    trigger_id: UUID


class DeleteTriggerHandler(BaseCommandHandler[DeleteTriggerCommand, None]):
    """Deletes a trigger."""

    trigger_ro_repo: TriggerRepositoryReadOnlyProtocol

    async def handle(self, command: DeleteTriggerCommand) -> None:
        """Delete a trigger."""
        async with self.new_uow() as uow:
            trigger = await self.trigger_ro_repo.get(command.trigger_id)
            await uow.delete(trigger)
