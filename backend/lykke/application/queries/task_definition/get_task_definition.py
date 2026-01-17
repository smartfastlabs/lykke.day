"""Query to get a task definition by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import TaskDefinitionRepositoryReadOnlyProtocol
from lykke.domain.entities import TaskDefinitionEntity


@dataclass(frozen=True)
class GetTaskDefinitionQuery(Query):
    """Query to get a task definition by ID."""

    task_definition_id: UUID


class GetTaskDefinitionHandler(BaseQueryHandler[GetTaskDefinitionQuery, TaskDefinitionEntity]):
    """Retrieves a single task definition by ID."""

    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol

    async def handle(self, query: GetTaskDefinitionQuery) -> TaskDefinitionEntity:
        """Get a single task definition by ID.

        Args:
            query: The query containing the task definition ID

        Returns:
            The task definition entity

        Raises:
            NotFoundError: If task definition not found
        """
        return await self.task_definition_ro_repo.get(query.task_definition_id)

