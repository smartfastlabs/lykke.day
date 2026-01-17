"""Command to create a new time block definition."""

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain.entities import TimeBlockDefinitionEntity


class CreateTimeBlockDefinitionHandler(BaseCommandHandler):
    """Creates a new time block definition."""

    async def run(
        self, time_block_definition: TimeBlockDefinitionEntity
    ) -> TimeBlockDefinitionEntity:
        """Create a new time block definition.

        Args:
            time_block_definition: The time block definition to create.

        Returns:
            The created time block definition.
        """
        async with self.new_uow() as uow:
            await uow.create(time_block_definition)
            return time_block_definition

