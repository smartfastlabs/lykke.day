"""Command to create a new time block definition."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import TimeBlockDefinitionEntity


@dataclass(frozen=True)
class CreateTimeBlockDefinitionCommand(Command):
    """Command to create a new time block definition."""

    time_block_definition: TimeBlockDefinitionEntity


class CreateTimeBlockDefinitionHandler(BaseCommandHandler[CreateTimeBlockDefinitionCommand, TimeBlockDefinitionEntity]):
    """Creates a new time block definition."""

    async def handle(self, command: CreateTimeBlockDefinitionCommand) -> TimeBlockDefinitionEntity:
        """Create a new time block definition.

        Args:
            command: The command containing the time block definition to create.

        Returns:
            The created time block definition.
        """
        async with self.new_uow() as uow:
            return await uow.create(command.time_block_definition)

