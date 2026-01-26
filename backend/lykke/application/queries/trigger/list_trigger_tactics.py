"""Query to list tactics linked to a trigger."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import TriggerRepositoryReadOnlyProtocol
from lykke.domain.entities import TacticEntity


@dataclass(frozen=True)
class ListTriggerTacticsQuery(Query):
    """Query to list tactics linked to a trigger."""

    trigger_id: UUID


class ListTriggerTacticsHandler(
    BaseQueryHandler[ListTriggerTacticsQuery, list[TacticEntity]]
):
    """Lists tactics linked to a trigger."""

    trigger_ro_repo: TriggerRepositoryReadOnlyProtocol

    async def handle(self, query: ListTriggerTacticsQuery) -> list[TacticEntity]:
        """List tactics linked to a trigger."""
        return await self.trigger_ro_repo.list_tactics_for_trigger(query.trigger_id)
