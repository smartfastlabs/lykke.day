"""Command to update an existing task definition."""

from dataclasses import asdict, fields, replace
from typing import Any, cast
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import TaskDefinitionEntity


class UpdateTaskDefinitionHandler:
    """Updates an existing task definition."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self,
        user_id: UUID,
        task_definition_id: UUID,
        task_definition_data: TaskDefinitionEntity,
    ) -> TaskDefinitionEntity:
        """Update an existing task definition.

        Args:
            user_id: The user making the request
            task_definition_id: The ID of the task definition to update
            task_definition_data: The updated task definition data

        Returns:
            The updated task definition entity

        Raises:
            NotFoundError: If task definition not found
        """
        async with self._uow_factory.create(user_id) as uow:
            # Get existing task definition
            existing = await uow.task_definition_rw_repo.get(task_definition_id)

            # Merge updates - both entities are dataclasses
            # Get all fields from task_definition_data that are not None
            task_definition_data_dict: dict[str, Any] = asdict(task_definition_data)

            # Filter out init=False fields (like _domain_events) - they can't be specified in replace()
            init_false_fields = {f.name for f in fields(existing) if not f.init}
            update_dict = {
                k: v
                for k, v in task_definition_data_dict.items()
                if v is not None and k not in init_false_fields
            }
            updated_any: Any = replace(existing, **update_dict)
            updated = cast(TaskDefinitionEntity, updated_any)

            # Ensure ID matches
            if hasattr(updated, "id"):
                object.__setattr__(updated, "id", task_definition_id)

            task_definition = await uow.task_definition_rw_repo.put(updated)
            await uow.commit()
            return task_definition

