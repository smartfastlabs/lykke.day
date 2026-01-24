"""Query to get a routine definition by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import RoutineDefinitionRepositoryReadOnlyProtocol
from lykke.domain.entities import RoutineDefinitionEntity


@dataclass(frozen=True)
class GetRoutineDefinitionQuery(Query):
    """Query to get a routine definition by ID."""

    routine_definition_id: UUID


class GetRoutineDefinitionHandler(
    BaseQueryHandler[GetRoutineDefinitionQuery, RoutineDefinitionEntity]
):
    """Retrieves a single routine definition by ID."""

    routine_definition_ro_repo: RoutineDefinitionRepositoryReadOnlyProtocol

    async def handle(
        self, query: GetRoutineDefinitionQuery
    ) -> RoutineDefinitionEntity:
        """Get a single routine definition by ID.

        Args:
            query: The query containing the routine definition ID

        Returns:
            The routine definition entity

        Raises:
            NotFoundError: If routine definition not found
        """
        return await self.routine_definition_ro_repo.get(query.routine_definition_id)
