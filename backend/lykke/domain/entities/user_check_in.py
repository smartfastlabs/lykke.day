"""UserCheckIn entity for wellbeing/status check-ins from user or LLM."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from lykke.domain import value_objects

from .base import BaseEntityObject


@dataclass(kw_only=True)
class UserCheckInEntity(BaseEntityObject):
    """A single check-in: user- or LLM-authored, with optional scores and text."""

    user_id: UUID
    source: value_objects.UserCheckInSource
    source_name: str | None = None  # e.g. todays_status, this_weeks_status
    source_metadata: dict[str, Any] = field(default_factory=dict)
    checkin_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    text: str | None = None
    scores: dict[str, Any] = field(default_factory=dict)  # arbitrary dimensions
