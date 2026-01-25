"""Push subscriptions table definition."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class PushSubscription(Base):
    """Push subscription table for storing web push subscriptions."""

    __tablename__ = "push_subscriptions"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    device_name = Column(String)
    endpoint = Column(String, nullable=False)
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (Index("idx_push_subscriptions_user_id", "user_id"),)
