"""Command to update an existing task definition."""

from dataclasses import asdict
from typing import Any
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import TaskDefinitionEntity
from planned.domain.value_objects import TaskDefinitionUpdateObject


class UpdateTaskDefinitionHandler:
    """Updates an existing task definition."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self,
        user_id: UUID,
        task_definition_id: UUID,
        update_data: TaskDefinitionUpdateObject,
    ) -> TaskDefinitionEntity:
        """Update an existing task definition.

        Args:
            user_id: The user making the request
            task_definition_id: The ID of the task definition to update
            update_data: The update data containing optional fields to update

        Returns:
            The updated task definition entity

        Raises:
            NotFoundError: If task definition not found
        """
        async with self._uow_factory.create(user_id) as uow:
            # Convert update_data to dict and filter out None values
            update_data_dict: dict[str, Any] = asdict(update_data)
            update_dict = {k: v for k, v in update_data_dict.items() if v is not None}

            # Apply updates directly to the database
            task_definition = await uow.task_definition_rw_repo.apply_updates(
                task_definition_id, **update_dict
            )
            await uow.commit()
            return task_definition
