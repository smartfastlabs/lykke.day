"""Routine definitions table definition."""

from sqlalchemy import Column, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class RoutineDefinition(Base):
    """RoutineDefinition table for storing recurring routine definitions."""

    __tablename__ = "routine_definitions"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # TaskCategory enum as string
    routine_definition_schedule = Column(JSONB, nullable=False)  # RecurrenceSchedule
    description = Column(String, nullable=False)
    time_window = Column(JSONB)  # TimeWindow
    tasks = Column(JSONB)  # list[RoutineDefinitionTask]

    __table_args__ = (Index("idx_routine_definitions_user_id", "user_id"),)
