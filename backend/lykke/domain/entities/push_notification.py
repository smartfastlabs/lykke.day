"""PushNotification entity for tracking sent push notifications."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from lykke.domain import value_objects

from .base import BaseEntityObject


@dataclass(kw_only=True)
class PushNotificationEntity(BaseEntityObject):
    """Entity representing a push notification that was sent.

    Tracks push notifications sent to users, including delivery status and
    smart-notification metadata (LLM reasoning, context snapshot, etc.).

    A single notification can be sent to multiple push subscriptions (devices),
    so push_subscription_ids is an array to avoid duplicating notification rows.
    """

    user_id: UUID
    push_subscription_ids: list[UUID] = field(default_factory=list)
    content: str  # JSON string of the notification payload
    status: str  # "success", "failed", "partial_failure", "skipped"
    error_message: str | None = None
    sent_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    # Smart notification metadata (optional for non-LLM pushes)
    message: str | None = None
    priority: str | None = None  # "high", "medium", "low"
    # LLM metadata is stored in llm_snapshot
    message_hash: str | None = None  # SHA256 hash for deduplication
    triggered_by: str | None = None  # "scheduled", "task_status_change", etc.
    llm_snapshot: value_objects.LLMRunResultSnapshot | None = None
