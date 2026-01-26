"""Command to create a new trigger."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import TriggerEntity


@dataclass(frozen=True)
class CreateTriggerCommand(Command):
    """Command to create a new trigger."""

    trigger: TriggerEntity


class CreateTriggerHandler(BaseCommandHandler[CreateTriggerCommand, TriggerEntity]):
    """Creates a new trigger."""

    async def handle(self, command: CreateTriggerCommand) -> TriggerEntity:
        """Create a new trigger."""
        async with self.new_uow() as uow:
            return await uow.create(command.trigger)
