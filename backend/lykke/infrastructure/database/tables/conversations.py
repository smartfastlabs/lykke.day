"""Conversations table definition."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class Conversation(Base):
    """Conversation table for storing AI chat conversations."""

    __tablename__ = "conversations"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    bot_personality_id = Column(
        PGUUID, ForeignKey("bot_personalities.id"), nullable=False
    )
    channel = Column(String, nullable=False)  # ConversationChannel enum as string
    status = Column(String, nullable=False)  # ConversationStatus enum as string
    llm_provider = Column(String, nullable=False)  # LLMProvider enum as string
    context = Column(JSONB)  # Conversation-specific metadata
    created_at = Column(DateTime, nullable=False)
    last_message_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_bot_personality_id", "bot_personality_id"),
        Index("idx_conversations_channel", "channel"),
        Index("idx_conversations_status", "status"),
    )
