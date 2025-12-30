"""Routines table definition."""

from sqlalchemy import Column, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class Routine(Base):
    """Routine table for storing recurring routines."""

    __tablename__ = "routines"

    uuid = Column(PGUUID, primary_key=True)
    user_uuid = Column(PGUUID, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # TaskCategory enum as string
    routine_schedule = Column(JSONB, nullable=False)  # RoutineSchedule
    description = Column(String, nullable=False)
    tasks = Column(JSONB)  # list[RoutineTask]

    __table_args__ = (Index("idx_routines_user_uuid", "user_uuid"),)

