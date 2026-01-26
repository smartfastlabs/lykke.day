"""Query to fetch a tactic by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import TacticRepositoryReadOnlyProtocol
from lykke.domain.entities import TacticEntity


@dataclass(frozen=True)
class GetTacticQuery(Query):
    """Query to fetch a tactic by ID."""

    tactic_id: UUID


class GetTacticHandler(BaseQueryHandler[GetTacticQuery, TacticEntity]):
    """Fetches a tactic by ID."""

    tactic_ro_repo: TacticRepositoryReadOnlyProtocol

    async def handle(self, query: GetTacticQuery) -> TacticEntity:
        """Fetch a tactic by ID."""
        return await self.tactic_ro_repo.get(query.tactic_id)
