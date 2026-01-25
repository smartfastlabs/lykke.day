"""Calendar entries table definition."""

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class CalendarEntry(Base):
    """CalendarEntry table for storing calendar entries."""

    __tablename__ = "calendar_entries"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)  # extracted from starts_at for querying
    name = Column(String, nullable=False)
    calendar_id = Column(PGUUID, ForeignKey("calendars.id"), nullable=False)
    calendar_entry_series_id = Column(
        PGUUID, ForeignKey("calendar_entry_series.id")
    )
    platform_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    status = Column(String, nullable=False)
    starts_at = Column(DateTime, nullable=False)
    frequency = Column(String, nullable=False)  # TaskFrequency enum as string
    category = Column(String)  # TaskCategory enum as string
    ends_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    actions = Column(JSONB)  # list[Action]

    __table_args__ = (
        Index("idx_calendar_entries_date", "date"),
        Index("idx_calendar_entries_calendar_id", "calendar_id"),
        Index("idx_calendar_entries_user_id", "user_id"),
        Index("idx_calendar_entries_series_id", "calendar_entry_series_id"),
    )
