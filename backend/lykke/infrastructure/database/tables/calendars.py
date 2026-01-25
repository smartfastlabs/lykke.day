"""Calendars table definition."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class Calendar(Base):
    """Calendar table for storing user calendars."""

    __tablename__ = "calendars"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    auth_token_id = Column(PGUUID, ForeignKey("auth_tokens.id"), nullable=False)
    platform_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    default_event_category = Column(String)
    last_sync_at = Column(DateTime)
    sync_subscription = Column(JSONB, nullable=True)  # SyncSubscription
    sync_subscription_id = Column(
        String, nullable=True
    )  # Denormalized for webhook lookups

    __table_args__ = (
        Index("idx_calendars_user_id", "user_id"),
        Index("idx_calendars_sync_subscription_id", "sync_subscription_id"),
    )
