"""Triggers table definition."""

from sqlalchemy import Column, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class Trigger(Base):
    """Trigger table for storing user-defined trigger definitions."""

    __tablename__ = "triggers"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    __table_args__ = (Index("idx_triggers_user_id", "user_id"),)
