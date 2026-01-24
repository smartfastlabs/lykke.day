"""Days table definition."""

from sqlalchemy import Column, Date, DateTime, Index, String, Text
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
    status = Column(String, nullable=False)  # DayStatus enum as string
    scheduled_at = Column(DateTime)
    starts_at = Column(DateTime)
    ends_at = Column(DateTime)
    time_blocks = Column(JSONB)  # list[DayTimeBlock]
    active_time_block_id = Column(PGUUID)  # UUID | None
    reminders = Column(JSONB)  # list[Reminder]
    brain_dump_items = Column(JSONB)  # list[BrainDumpItem]
    high_level_plan = Column(JSONB)  # HighLevelPlan | None

    __table_args__ = (
        Index("idx_days_date", "date"),
        Index("idx_days_user_id", "user_id"),
    )
