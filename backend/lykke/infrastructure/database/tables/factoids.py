"""Factoids table definition."""

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.types import Float

from .base import Base


class Factoid(Base):
    """Factoid table for storing conversation factoids."""

    __tablename__ = "factoids"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    conversation_id = Column(PGUUID, nullable=True)  # None for global factoids
    factoid_type = Column(String, nullable=False)  # FactoidType enum as string
    criticality = Column(String, nullable=False)  # FactoidCriticality enum as string
    content = Column(Text, nullable=False)  # Factoid content
    embedding: Column[ARRAY[Float]] = Column(
        ARRAY(Float), nullable=True
    )  # For semantic search (vector embeddings)
    ai_suggested = Column(
        String, nullable=False, default="false"
    )  # AI marked as important (stored as string for compatibility)
    user_confirmed = Column(
        String, nullable=False, default="false"
    )  # User confirmed criticality (stored as string for compatibility)
    last_accessed = Column(DateTime, nullable=False)
    access_count = Column(Integer, nullable=False, default=0)
    meta = Column(JSONB)  # Additional meta
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_factoids_user_id", "user_id"),
        Index("idx_factoids_conversation_id", "conversation_id"),
        Index("idx_factoids_criticality", "criticality"),
        Index("idx_factoids_factoid_type", "factoid_type"),
        Index("idx_factoids_user_criticality", "user_id", "criticality"),
    )
