"""Protocols for reading/streaming the structured log backlog used by admin.

This backlog is produced by `StructuredLogGateway` and stored in Redis as:
- a sorted-set backlog (`STRUCTURED_LOG_BACKLOG_KEY`)
- a pub/sub stream (`STRUCTURED_LOG_STREAM_CHANNEL`)

Despite legacy naming in the API (`/admin/events`), these are *structured log*
events, not the core domain event bus.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, Self


@dataclass(frozen=True, kw_only=True)
class StructuredLogBacklogItem:
    """A single entry in the structured log backlog."""

    id: str
    event_type: str
    event_data: dict[str, Any]
    stored_at: datetime


@dataclass(frozen=True, kw_only=True)
class StructuredLogBacklogListResult:
    """Paginated result for structured log backlog listing."""

    items: list[StructuredLogBacklogItem]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool


class StructuredLogBacklogGatewayProtocol(Protocol):
    """Protocol for listing structured log backlog events."""

    async def list_events(
        self,
        *,
        search: str | None,
        user_id: str | None,
        event_type: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        limit: int,
        offset: int,
    ) -> StructuredLogBacklogListResult:
        """List backlog entries with optional filtering and pagination."""
        ...


class StructuredLogBacklogStreamSubscription(Protocol):
    """Subscription to the structured log backlog stream."""

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None: ...

    async def get_message(self, timeout: float | None = None) -> dict[str, Any] | None:
        """Get the next stream message, or None if timeout occurred."""
        ...

    async def close(self) -> None:
        """Close the subscription."""
        ...


class StructuredLogBacklogStreamGatewayProtocol(Protocol):
    """Protocol for subscribing to structured log backlog stream."""

    def subscribe_to_stream(self) -> StructuredLogBacklogStreamSubscription:
        """Subscribe to the stream of new backlog events."""
        ...
