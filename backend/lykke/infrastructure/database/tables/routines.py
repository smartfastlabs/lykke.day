"""Routines table definition."""

from sqlalchemy import Column, Date, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class Routine(Base):
    """Routine table for storing scheduled routine instances."""

    __tablename__ = "routines"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    routine_definition_id = Column(
        PGUUID, ForeignKey("routine_definitions.id"), nullable=False
    )
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # TaskCategory enum as string
    description = Column(String, nullable=False)
    time_window = Column(JSONB)  # TimeWindow | None

    __table_args__ = (
        Index("idx_routines_date", "date"),
        Index("idx_routines_routine_definition_id", "routine_definition_id"),
        Index("idx_routines_user_id", "user_id"),
    )
