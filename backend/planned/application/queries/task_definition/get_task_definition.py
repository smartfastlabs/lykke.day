"""Query to get a task definition by ID."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import TaskDefinitionEntity


class GetTaskDefinitionHandler:
    """Retrieves a single task definition by ID."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self, user_id: UUID, task_definition_id: UUID
    ) -> TaskDefinitionEntity:
        """Get a single task definition by ID.

        Args:
            user_id: The user making the request
            task_definition_id: The ID of the task definition to retrieve

        Returns:
            The task definition entity

        Raises:
            NotFoundError: If task definition not found
        """
        async with self._uow_factory.create(user_id) as uow:
            return await uow.task_definitions.get(task_definition_id)

