"""Protocols for reading the per-user domain event backlog stored in Redis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class DomainEventBacklogItem:
    """A single entry in the domain event backlog."""

    id: str
    event_type: str
    event_data: dict[str, Any]
    stored_at: datetime


@dataclass(frozen=True, kw_only=True)
class DomainEventBacklogListResult:
    """Paginated result for domain event backlog listing."""

    items: list[DomainEventBacklogItem]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool


class DomainEventBacklogGatewayProtocol(Protocol):
    """Protocol for listing domain event backlog entries for a user."""

    async def list_events(
        self,
        *,
        user_id: UUID,
        search: str | None,
        event_type: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        limit: int,
        offset: int,
    ) -> DomainEventBacklogListResult:
        """List backlog entries with optional filtering and pagination."""
        ...
