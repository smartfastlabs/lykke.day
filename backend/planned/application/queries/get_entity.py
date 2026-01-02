"""Generic query to get a single entity by ID."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from planned.application.queries.base import Query, QueryHandler
from planned.application.unit_of_work import UnitOfWorkFactory


@dataclass(frozen=True)
class GetEntityQuery(Query):
    """Query to retrieve a single entity by ID.

    Attributes:
        user_id: The user making the request
        entity_id: The ID of the entity to retrieve
        repository_name: Name of the repository on UoW (e.g., "days", "tasks")
    """

    user_id: UUID
    entity_id: UUID
    repository_name: str


class GetEntityHandler(QueryHandler[GetEntityQuery, Any]):
    """Handles GetEntityQuery - retrieves a single entity by ID."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, query: GetEntityQuery) -> Any:
        """Execute the query.

        Args:
            query: The get entity query

        Returns:
            The entity

        Raises:
            NotFoundError: If entity not found
        """
        async with self._uow_factory.create(query.user_id) as uow:
            repo = getattr(uow, query.repository_name)
            return await repo.get(query.entity_id)

