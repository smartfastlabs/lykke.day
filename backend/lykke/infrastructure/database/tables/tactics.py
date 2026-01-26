"""Tactics table definition."""

from sqlalchemy import Column, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class Tactic(Base):
    """Tactic table for storing user-defined tactic definitions."""

    __tablename__ = "tactics"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    __table_args__ = (Index("idx_tactics_user_id", "user_id"),)
