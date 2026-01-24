"""Factoid schema."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from .base import BaseEntitySchema


class FactoidSchema(BaseEntitySchema):
    """Schema for Factoid entity."""

    user_id: UUID
    conversation_id: UUID | None = None
    factoid_type: str
    criticality: str
    content: str
    embedding: list[float] | None = None
    ai_suggested: bool = False
    user_confirmed: bool = False
    last_accessed: datetime
    access_count: int = 0
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
