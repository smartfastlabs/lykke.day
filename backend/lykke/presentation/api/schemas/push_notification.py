"""Push notification schema."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from .base import BaseEntitySchema


class PushNotificationSchema(BaseEntitySchema):
    """API schema for PushNotification entity."""

    user_id: UUID
    push_subscription_ids: list[UUID] = Field(default_factory=list)
    content: str
    status: str
    error_message: str | None = None
    sent_at: datetime
    message: str | None = None
    priority: str | None = None
    message_hash: str | None = None
    triggered_by: str | None = None
    llm_snapshot: dict[str, Any] | None = None
