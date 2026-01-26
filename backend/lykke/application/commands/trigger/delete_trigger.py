"""Command to delete a trigger."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command


@dataclass(frozen=True)
class DeleteTriggerCommand(Command):
    """Command to delete a trigger."""

    trigger_id: UUID


class DeleteTriggerHandler(BaseCommandHandler[DeleteTriggerCommand, None]):
    """Deletes a trigger."""

    async def handle(self, command: DeleteTriggerCommand) -> None:
        """Delete a trigger."""
        async with self.new_uow() as uow:
            trigger = await uow.trigger_ro_repo.get(command.trigger_id)
            await uow.delete(trigger)
