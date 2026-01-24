"""Push notifications table definition."""

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID

from .base import Base


class PushNotification(Base):
    """Push notification table for tracking sent push notifications."""

    __tablename__ = "push_notifications"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    push_subscription_ids: Column[list[PGUUID]] = Column(ARRAY(PGUUID), nullable=False)
    content = Column(Text, nullable=False)  # JSON string of the notification payload
    status = Column(
        String, nullable=False
    )  # "success", "failed", "partial_failure", "skipped"
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=False)
    # Smart notification metadata (optional for non-LLM pushes)
    message = Column(Text, nullable=True)
    priority = Column(String, nullable=True)  # "high", "medium", "low"
    reason = Column(Text, nullable=True)  # LLM's reasoning
    day_context_snapshot = Column(JSONB, nullable=True)
    message_hash = Column(String, nullable=True)  # SHA256 hash for deduplication
    triggered_by = Column(
        String, nullable=True
    )  # "scheduled", "task_status_change", etc.
    llm_provider = Column(String, nullable=True)  # "anthropic", "openai", etc.

    __table_args__ = (
        Index("idx_push_notifications_user_id", "user_id"),
        Index("idx_push_notifications_status", "status"),
        Index("idx_push_notifications_sent_at", "sent_at"),
        Index("idx_push_notifications_message_hash", "message_hash"),
        Index("idx_push_notifications_user_sent_at", "user_id", "sent_at"),
        Index("idx_push_notifications_message_hash_sent_at", "message_hash", "sent_at"),
    )
