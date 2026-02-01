"""Query handler for listing per-user domain event backlog entries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from lykke.application.gateways.domain_event_backlog_protocol import (
    DomainEventBacklogGatewayProtocol,
    DomainEventBacklogListResult,
)
from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.unit_of_work import ReadOnlyRepositories


@dataclass(frozen=True)
class ListDomainEventsQuery(Query):
    """List domain event backlog entries for the current user."""

    search: str | None = None
    event_type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    limit: int = 100
    offset: int = 0


class ListDomainEventsHandler(
    BaseQueryHandler[ListDomainEventsQuery, DomainEventBacklogListResult]
):
    """Handler for listing per-user domain event backlog entries."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        user_id: UUID,
        backlog_gateway: DomainEventBacklogGatewayProtocol,
    ) -> None:
        super().__init__(ro_repos, user_id)
        self._backlog_gateway = backlog_gateway

    async def handle(
        self, query: ListDomainEventsQuery
    ) -> DomainEventBacklogListResult:
        """Return the current user's domain event backlog."""
        return await self._backlog_gateway.list_events(
            user_id=self.user_id,
            search=query.search,
            event_type=query.event_type,
            start_time=query.start_time,
            end_time=query.end_time,
            limit=query.limit,
            offset=query.offset,
        )
