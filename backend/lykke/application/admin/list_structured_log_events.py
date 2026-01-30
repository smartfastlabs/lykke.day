"""Admin application operation for listing structured log backlog events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from lykke.application.gateways.structured_log_backlog_protocol import (
    StructuredLogBacklogGatewayProtocol,
    StructuredLogBacklogListResult,
)


@dataclass(frozen=True, kw_only=True)
class ListStructuredLogEventsQuery:
    """List structured log backlog events with optional filters."""

    search: str | None = None
    user_id: str | None = None
    event_type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    limit: int = 100
    offset: int = 0


class ListStructuredLogEventsHandler:
    """Handler for listing structured log backlog events."""

    def __init__(self, backlog_gateway: StructuredLogBacklogGatewayProtocol) -> None:
        self._backlog_gateway = backlog_gateway

    async def handle(
        self, query: ListStructuredLogEventsQuery
    ) -> StructuredLogBacklogListResult:
        return await self._backlog_gateway.list_events(
            search=query.search,
            user_id=query.user_id,
            event_type=query.event_type,
            start_time=query.start_time,
            end_time=query.end_time,
            limit=query.limit,
            offset=query.offset,
        )
