"""Query to get a routine by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import RoutineRepositoryReadOnlyProtocol
from lykke.domain.entities import RoutineEntity


@dataclass(frozen=True)
class GetRoutineQuery(Query):
    """Query to get a routine by ID."""

    routine_id: UUID


class GetRoutineHandler(BaseQueryHandler[GetRoutineQuery, RoutineEntity]):
    """Retrieves a single routine by ID."""

    routine_ro_repo: RoutineRepositoryReadOnlyProtocol

    async def handle(self, query: GetRoutineQuery) -> RoutineEntity:
        """Get a single routine by ID.

        Args:
            query: The query containing the routine ID

        Returns:
            The routine entity

        Raises:
            NotFoundError: If routine not found
        """
        return await self.routine_ro_repo.get(query.routine_id)

