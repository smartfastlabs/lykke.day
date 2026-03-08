"""User check-ins table definition."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class UserCheckIn(Base):
    """User check-ins: user- or LLM-authored status/wellbeing entries."""

    __tablename__ = "user_check_ins"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    source = Column(String, nullable=False)  # UserCheckInSource enum as string
    source_name = Column(String, nullable=True)  # e.g. todays_status
    source_metadata = Column(JSONB, nullable=True)  # usecase, provider, etc.
    checkin_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    text = Column(Text, nullable=True)
    scores = Column(JSONB, nullable=True)  # arbitrary dimensions: { "mood": 62, ... }

    __table_args__ = (
        Index("idx_user_check_ins_user_id_checkin_at", "user_id", "checkin_at"),
        Index("idx_user_check_ins_user_id_source_checkin_at", "user_id", "source", "checkin_at"),
        Index("idx_user_check_ins_user_id", "user_id"),
    )


user_check_ins_tbl = UserCheckIn.__table__
