"""Command to delete a task definition."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory


class DeleteTaskDefinitionHandler:
    """Deletes a task definition."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self, user_id: UUID, task_definition_id: UUID
    ) -> None:
        """Delete a task definition.

        Args:
            user_id: The user making the request
            task_definition_id: The ID of the task definition to delete

        Raises:
            NotFoundError: If task definition not found
        """
        async with self._uow_factory.create(user_id) as uow:
            task_definition = await uow.task_definition_rw_repo.get(task_definition_id)
            await uow.task_definition_rw_repo.delete(task_definition)
            await uow.commit()

