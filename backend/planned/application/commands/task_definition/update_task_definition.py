"""Command to update an existing task definition."""

from dataclasses import asdict
from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.infrastructure import data_objects
from planned.domain.value_objects import TaskDefinitionUpdateObject


class UpdateTaskDefinitionHandler(BaseCommandHandler):
    """Updates an existing task definition."""

    async def run(
        self,
        task_definition_id: UUID,
        update_data: TaskDefinitionUpdateObject,
    ) -> data_objects.TaskDefinition:
        """Update an existing task definition.

        Args:
            task_definition_id: The ID of the task definition to update
            update_data: The update data containing optional fields to update

        Returns:
            The updated task definition data object

        Raises:
            NotFoundError: If task definition not found
        """
        async with self.new_uow() as uow:
            # Get the existing task definition
            task_definition = await uow.task_definition_ro_repo.get(task_definition_id)

            # Convert update object to dict and filter out None values
            update_dict = asdict(update_data)
            update_dict = {k: v for k, v in update_dict.items() if v is not None}

            # Apply updates using clone
            updated_task_definition = task_definition.clone(**update_dict)

            # Add to UoW for saving
            uow.add(updated_task_definition)
            return updated_task_definition
