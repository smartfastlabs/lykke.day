"""UseCase config entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from .base import BaseEntityObject


@dataclass(kw_only=True)
class UseCaseConfigEntity(BaseEntityObject):
    """User-specific configuration for a usecase."""

    user_id: UUID
    usecase: str
    config: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
