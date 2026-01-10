"""Command to update an existing time block definition."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain.data_objects import TimeBlockDefinition
from lykke.domain.value_objects import TimeBlockDefinitionUpdateObject


class UpdateTimeBlockDefinitionHandler(BaseCommandHandler):
    """Updates an existing time block definition."""

    async def run(
        self,
        time_block_definition_id: UUID,
        update_data: TimeBlockDefinitionUpdateObject,
    ) -> TimeBlockDefinition:
        """Update an existing time block definition.

        Args:
            time_block_definition_id: The ID of the time block definition to update.
            update_data: The update data containing optional fields.

        Returns:
            The updated time block definition.
        """
        async with self.new_uow() as uow:
            # Get the existing time block definition
            time_block_definition = await uow.time_block_definition_ro_repo.get(
                time_block_definition_id
            )

            # Apply updates
            updated_fields = update_data.model_dump(exclude_unset=True)
            for field, value in updated_fields.items():
                setattr(time_block_definition, field, value)

            # Add entity to UoW for saving
            uow.add(time_block_definition)
            return time_block_definition

