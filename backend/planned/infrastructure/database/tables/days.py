"""Days table definition."""

from sqlalchemy import Column, Date, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class Day(Base):
    """Day table for storing scheduled days."""

    __tablename__ = "days"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    date = Column(Date, nullable=False)
    template = Column(JSONB)  # DayTemplate | None
    tags = Column(JSONB)  # list[DayTag]
    alarm = Column(JSONB)  # Alarm | None
    status = Column(String, nullable=False)  # DayStatus enum as string
    scheduled_at = Column(DateTime)

    __table_args__ = (
        Index("idx_days_date", "date"),
        Index("idx_days_user_id", "user_id"),
    )

