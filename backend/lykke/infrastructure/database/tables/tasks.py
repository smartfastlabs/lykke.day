"""Tasks table definition."""

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class Task(Base):
    """Task table for storing scheduled tasks."""

    __tablename__ = "tasks"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)  # extracted from scheduled_date for querying
    scheduled_date = Column(Date, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # TaskStatus enum as string
    type = Column(String, nullable=False)  # TaskType enum as string
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)  # TaskCategory enum as string
    frequency = Column(String, nullable=False)  # TaskFrequency enum as string
    completed_at = Column(DateTime)
    snoozed_until = Column(DateTime)
    time_window = Column(JSONB)  # TimeWindow | None
    routine_definition_id = Column(PGUUID, ForeignKey("routine_definitions.id"))
    tags = Column(JSONB)  # list[TaskTag]
    actions = Column(JSONB)  # list[Action]

    __table_args__ = (
        Index("idx_tasks_date", "date"),
        Index("idx_tasks_routine_definition_id", "routine_definition_id"),
        Index("idx_tasks_user_id", "user_id"),
    )
