"""Query handler to get a time block definition by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import TimeBlockDefinitionRepositoryReadOnlyProtocol
from lykke.domain.entities import TimeBlockDefinitionEntity


@dataclass(frozen=True)
class GetTimeBlockDefinitionQuery(Query):
    """Query to get a time block definition by ID."""

    time_block_definition_id: UUID


class GetTimeBlockDefinitionHandler(
    BaseQueryHandler[GetTimeBlockDefinitionQuery, TimeBlockDefinitionEntity]
):
    """Query handler to get a single time block definition by ID."""

    time_block_definition_ro_repo: TimeBlockDefinitionRepositoryReadOnlyProtocol

    async def handle(
        self, query: GetTimeBlockDefinitionQuery
    ) -> TimeBlockDefinitionEntity:
        """Get a time block definition by ID."""
        return await self.time_block_definition_ro_repo.get(
            query.time_block_definition_id
        )
