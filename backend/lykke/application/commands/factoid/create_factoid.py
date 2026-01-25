"""Command to create a new factoid."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import FactoidEntity


@dataclass(frozen=True)
class CreateFactoidCommand(Command):
    """Command to create a new factoid."""

    factoid: FactoidEntity


class CreateFactoidHandler(BaseCommandHandler[CreateFactoidCommand, FactoidEntity]):
    """Creates a new factoid."""

    async def handle(self, command: CreateFactoidCommand) -> FactoidEntity:
        """Create a new factoid.

        Args:
            command: The command containing the factoid entity to create

        Returns:
            The created factoid entity
        """
        async with self.new_uow() as uow:
            return await uow.create(command.factoid)
