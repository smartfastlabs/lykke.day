"""Query to get a brain dump by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import BrainDumpRepositoryReadOnlyProtocol
from lykke.domain.entities import BrainDumpEntity


@dataclass(frozen=True)
class GetBrainDumpQuery(Query):
    """Query to get a brain dump by ID."""

    item_id: UUID


class GetBrainDumpHandler(BaseQueryHandler[GetBrainDumpQuery, BrainDumpEntity]):
    """Retrieves a single brain dump by ID."""

    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol

    async def handle(self, query: GetBrainDumpQuery) -> BrainDumpEntity:
        """Get a single brain dump by ID."""
        return await self.brain_dump_ro_repo.get(query.item_id)
