"""Command to update an existing time block definition."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import TimeBlockDefinitionEntity
from lykke.domain.events.time_block_definition_events import (
    TimeBlockDefinitionUpdatedEvent,
)
from lykke.domain.value_objects import TimeBlockDefinitionUpdateObject


@dataclass(frozen=True)
class UpdateTimeBlockDefinitionCommand(Command):
    """Command to update an existing time block definition."""

    time_block_definition_id: UUID
    update_data: TimeBlockDefinitionUpdateObject


class UpdateTimeBlockDefinitionHandler(BaseCommandHandler[UpdateTimeBlockDefinitionCommand, TimeBlockDefinitionEntity]):
    """Updates an existing time block definition."""

    async def handle(self, command: UpdateTimeBlockDefinitionCommand) -> TimeBlockDefinitionEntity:
        """Update an existing time block definition.

        Args:
            command: The command containing the time block definition ID and update data.

        Returns:
            The updated time block definition.
        """
        async with self.new_uow() as uow:
            # Get the existing time block definition
            time_block_definition = await uow.time_block_definition_ro_repo.get(
                command.time_block_definition_id
            )

            # Apply updates using domain method (adds EntityUpdatedEvent)
            time_block_definition = time_block_definition.apply_update(
                command.update_data, TimeBlockDefinitionUpdatedEvent
            )

            # Add entity to UoW for saving
            uow.add(time_block_definition)
            return time_block_definition

