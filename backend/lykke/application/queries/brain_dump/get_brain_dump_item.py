"""Query to get a brain dump item by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import BrainDumpRepositoryReadOnlyProtocol
from lykke.domain.entities import BrainDumpEntity


@dataclass(frozen=True)
class GetBrainDumpItemQuery(Query):
    """Query to get a brain dump item by ID."""

    item_id: UUID


class GetBrainDumpItemHandler(
    BaseQueryHandler[GetBrainDumpItemQuery, BrainDumpEntity]
):
    """Retrieves a single brain dump item by ID."""

    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol

    async def handle(self, query: GetBrainDumpItemQuery) -> BrainDumpEntity:
        """Get a single brain dump item by ID."""
        return await self.brain_dump_ro_repo.get(query.item_id)
