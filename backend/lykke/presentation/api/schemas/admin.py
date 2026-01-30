"""Admin schemas for API responses."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DomainEventSchema(BaseModel):
    """Schema for a single structured log backlog entry.

    Note: The endpoint is historically named `/admin/events`, but these entries
    are produced by the structured logger backlog, not the core domain-event bus.
    """

    id: str
    event_type: str
    event_data: dict[str, Any]
    stored_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @property
    def user_id(self) -> UUID | None:
        """Extract user_id from event_data if present."""
        user_id = self.event_data.get("user_id")
        if user_id:
            return UUID(user_id) if isinstance(user_id, str) else user_id
        return None

    @property
    def occurred_at(self) -> datetime | None:
        """Extract occurred_at from event_data if present."""
        occurred_at = self.event_data.get("occurred_at")
        if occurred_at:
            return (
                datetime.fromisoformat(occurred_at)
                if isinstance(occurred_at, str)
                else occurred_at
            )
        return None


class DomainEventListResponse(BaseModel):
    """Schema for paginated structured log backlog list response."""

    items: list[DomainEventSchema]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool

    model_config = ConfigDict(from_attributes=True)
