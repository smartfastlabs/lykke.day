"""Command to bulk create task definitions."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import TaskDefinitionEntity


class BulkCreateTaskDefinitionsHandler:
    """Creates multiple task definitions."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self, user_id: UUID, task_definitions: tuple[TaskDefinitionEntity, ...]
    ) -> list[TaskDefinitionEntity]:
        """Create multiple task definitions.

        Args:
            user_id: The user making the request
            task_definitions: Tuple of task definition entities to create

        Returns:
            List of created task definition entities
        """
        if not task_definitions:
            return []

        async with self._uow_factory.create(user_id) as uow:
            created = await uow.task_definitions.insert_many(*task_definitions)
            await uow.commit()
            return created

