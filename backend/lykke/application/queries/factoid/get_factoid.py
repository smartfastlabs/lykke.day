"""Query to get a factoid by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import FactoidRepositoryReadOnlyProtocol
from lykke.domain.entities import FactoidEntity


@dataclass(frozen=True)
class GetFactoidQuery(Query):
    """Query to get a factoid by ID."""

    factoid_id: UUID


class GetFactoidHandler(BaseQueryHandler[GetFactoidQuery, FactoidEntity]):
    """Retrieves a single factoid by ID."""

    factoid_ro_repo: FactoidRepositoryReadOnlyProtocol

    async def handle(self, query: GetFactoidQuery) -> FactoidEntity:
        """Get a single factoid by ID.

        Args:
            query: The query containing the factoid ID

        Returns:
            The factoid entity

        Raises:
            NotFoundError: If factoid not found
        """
        return await self.factoid_ro_repo.get(query.factoid_id)
