"""Trigger tactics join table definition."""

from sqlalchemy import Column, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class TriggerTactic(Base):
    """Join table for linking triggers to tactics."""

    __tablename__ = "trigger_tactics"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(
        PGUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    trigger_id = Column(
        PGUUID, ForeignKey("triggers.id", ondelete="CASCADE"), nullable=False
    )
    tactic_id = Column(
        PGUUID, ForeignKey("tactics.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "trigger_id", "tactic_id"),
        Index("idx_trigger_tactics_user_id", "user_id"),
        Index("idx_trigger_tactics_trigger_id", "trigger_id"),
        Index("idx_trigger_tactics_tactic_id", "tactic_id"),
    )
