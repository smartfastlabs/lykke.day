"""Messages table definition."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class Message(Base):
    """Message table for storing individual messages."""

    __tablename__ = "messages"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # MessageRole enum as string
    type = Column(
        String, nullable=False, server_default="UNKNOWN"
    )  # MessageType enum as string
    content = Column(Text, nullable=False)  # Message text
    meta = Column(JSONB)  # Provider-specific data
    llm_run_result = Column(JSONB, nullable=True)  # LLMRunResultSnapshot
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_messages_user_id", "user_id"),
        Index("idx_messages_created_at", "created_at"),
        Index("idx_messages_user_created", "user_id", "created_at"),
    )
