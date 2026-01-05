"""Command to update an existing task definition."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import TaskDefinitionEntity
from planned.domain.value_objects import TaskDefinitionUpdateObject


class UpdateTaskDefinitionHandler:
    """Updates an existing task definition."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

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
        async with self._uow_factory.create(self.user_id) as uow:
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
