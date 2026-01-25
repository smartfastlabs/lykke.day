"""Bot personalities table definition."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class BotPersonality(Base):
    """Bot personality table for storing AI bot personality configurations."""

    __tablename__ = "bot_personalities"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(
        PGUUID, ForeignKey("users.id"), nullable=True
    )  # None for system defaults
    name = Column(String, nullable=False)
    base_bot_personality_id = Column(
        PGUUID, ForeignKey("bot_personalities.id"), nullable=True
    )  # Inherits from base
    system_prompt = Column(Text, nullable=False)  # Base personality instructions
    user_amendments = Column(Text, nullable=False, default="")  # User customizations
    meta = Column(JSONB)  # Additional config
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_bot_personalities_user_id", "user_id"),
        Index("idx_bot_personalities_base_id", "base_bot_personality_id"),
    )
