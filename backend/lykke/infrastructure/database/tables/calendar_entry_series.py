"""Calendar entry series table definition."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class CalendarEntrySeries(Base):
    """CalendarEntrySeries table for storing recurring event series."""

    __tablename__ = "calendar_entry_series"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    calendar_id = Column(PGUUID, ForeignKey("calendars.id"), nullable=False)
    name = Column(String, nullable=False)
    platform_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    frequency = Column(String, nullable=False)  # TaskFrequency enum as string
    event_category = Column(String)  # EventCategory enum as string
    recurrence = Column(JSONB)  # Recurrence rules from provider (e.g., Google)
    starts_at = Column(DateTime)
    ends_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_calendar_entry_series_user_id", "user_id"),
        Index("idx_calendar_entry_series_calendar_id", "calendar_id"),
        Index("idx_calendar_entry_series_platform_id", "platform_id"),
    )
