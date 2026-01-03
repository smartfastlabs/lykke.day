"""Command to create a new task definition."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import TaskDefinitionEntity


class CreateTaskDefinitionHandler:
    """Creates a new task definition."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self, user_id: UUID, task_definition: TaskDefinitionEntity
    ) -> TaskDefinitionEntity:
        """Create a new task definition.

        Args:
            user_id: The user making the request
            task_definition: The task definition entity to create

        Returns:
            The created task definition entity
        """
        async with self._uow_factory.create(user_id) as uow:
            created_task_definition = await uow.task_definition_rw_repo.put(
                task_definition
            )
            await uow.commit()
            return created_task_definition
