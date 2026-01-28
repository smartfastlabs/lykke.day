"""Domain events for notification streaming."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from lykke.domain.events.base import DomainEvent

__all__ = ["KioskNotificationEvent"]


@dataclass(frozen=True, kw_only=True)
class KioskNotificationEvent(DomainEvent):
    """Event raised when a kiosk notification is emitted."""

    message: str
    category: str
    message_hash: str
    created_at: datetime
    triggered_by: str | None = None
