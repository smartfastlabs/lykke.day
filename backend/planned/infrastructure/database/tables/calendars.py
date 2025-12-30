"""Calendars table definition."""

from sqlalchemy import Column, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class Calendar(Base):
    """Calendar table for storing user calendars."""

    __tablename__ = "calendars"

    uuid = Column(PGUUID, primary_key=True)
    user_uuid = Column(PGUUID, nullable=False)
    name = Column(String, nullable=False)
    auth_token_uuid = Column(PGUUID, nullable=False)
    platform_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    last_sync_at = Column(DateTime)

    __table_args__ = (Index("idx_calendars_user_uuid", "user_uuid"),)

