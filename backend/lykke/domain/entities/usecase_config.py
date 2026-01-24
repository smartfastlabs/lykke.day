"""UseCase config entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .base import BaseEntityObject

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(kw_only=True)
class UseCaseConfigEntity(BaseEntityObject):
    """User-specific configuration for a usecase."""

    user_id: UUID
    usecase: str
    config: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
