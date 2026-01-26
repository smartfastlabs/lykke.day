"""Command to create a new tactic."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import TacticEntity


@dataclass(frozen=True)
class CreateTacticCommand(Command):
    """Command to create a new tactic."""

    tactic: TacticEntity


class CreateTacticHandler(BaseCommandHandler[CreateTacticCommand, TacticEntity]):
    """Creates a new tactic."""

    async def handle(self, command: CreateTacticCommand) -> TacticEntity:
        """Create a new tactic."""
        async with self.new_uow() as uow:
            return await uow.create(command.tactic)
