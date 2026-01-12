"""Messages table definition."""

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class Message(Base):
    """Message table for storing individual messages in conversations."""

    __tablename__ = "messages"

    id = Column(PGUUID, primary_key=True)
    conversation_id = Column(PGUUID, nullable=False)
    role = Column(String, nullable=False)  # MessageRole enum as string
    content = Column(Text, nullable=False)  # Message text
    meta = Column(JSONB)  # Provider-specific data
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_created_at", "created_at"),
        Index("idx_messages_conversation_created", "conversation_id", "created_at"),
    )
