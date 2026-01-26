"""Query to fetch a trigger by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import TriggerRepositoryReadOnlyProtocol
from lykke.domain.entities import TriggerEntity


@dataclass(frozen=True)
class GetTriggerQuery(Query):
    """Query to fetch a trigger by ID."""

    trigger_id: UUID


class GetTriggerHandler(BaseQueryHandler[GetTriggerQuery, TriggerEntity]):
    """Fetches a trigger by ID."""

    trigger_ro_repo: TriggerRepositoryReadOnlyProtocol

    async def handle(self, query: GetTriggerQuery) -> TriggerEntity:
        """Fetch a trigger by ID."""
        return await self.trigger_ro_repo.get(query.trigger_id)
