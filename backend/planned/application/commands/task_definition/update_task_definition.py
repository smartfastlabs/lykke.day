"""Command to update an existing task definition."""

from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.domain.entities import TaskDefinitionEntity
from planned.domain.value_objects import TaskDefinitionUpdateObject


class UpdateTaskDefinitionHandler(BaseCommandHandler):
    """Updates an existing task definition."""

    async def run(
        self,
        task_definition_id: UUID,
        update_data: TaskDefinitionUpdateObject,
    ) -> TaskDefinitionEntity:
        """Update an existing task definition.

        Args:
            task_definition_id: The ID of the task definition to update
            update_data: The update data containing optional fields to update

        Returns:
            The updated task definition entity

        Raises:
            NotFoundError: If task definition not found
        """
        async with self.new_uow() as uow:
            # Get the existing task definition
            task_definition = await uow.task_definition_ro_repo.get(task_definition_id)

            # Apply updates using domain method (adds EntityUpdatedEvent)
            from planned.domain.events.task_events import TaskDefinitionUpdatedEvent

            task_definition = task_definition.apply_update(
                update_data, TaskDefinitionUpdatedEvent
            )

            # Add entity to UoW for saving
            uow.add(task_definition)
            return task_definition
