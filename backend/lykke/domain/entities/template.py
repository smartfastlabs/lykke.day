from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from .base import BaseEntityObject


@dataclass(kw_only=True)
class TemplateEntity(BaseEntityObject):
    """User override for a system prompt template."""

    user_id: UUID
    usecase: str
    key: str
    name: str
    description: str | None = None
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
