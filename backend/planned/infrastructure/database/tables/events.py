"""Events table definition."""

from sqlalchemy import Column, Date, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class Event(Base):
    """Event table for storing calendar events."""

    __tablename__ = "events"

    uuid = Column(PGUUID, primary_key=True)
    user_uuid = Column(PGUUID, nullable=False)
    date = Column(Date, nullable=False)  # extracted from starts_at for querying
    name = Column(String, nullable=False)
    calendar_uuid = Column(PGUUID, nullable=False)
    platform_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    status = Column(String, nullable=False)
    starts_at = Column(DateTime, nullable=False)
    frequency = Column(String, nullable=False)  # TaskFrequency enum as string
    ends_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    people = Column(JSONB)  # list[Person]
    actions = Column(JSONB)  # list[Action]

    __table_args__ = (
        Index("idx_events_date", "date"),
        Index("idx_events_calendar_uuid", "calendar_uuid"),
        Index("idx_events_user_uuid", "user_uuid"),
    )

