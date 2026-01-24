"""Tasks table definition."""

from sqlalchemy import Column, Date, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class Task(Base):
    """Task table for storing scheduled tasks."""

    __tablename__ = "tasks"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    date = Column(Date, nullable=False)  # extracted from scheduled_date for querying
    scheduled_date = Column(Date, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # TaskStatus enum as string
    type = Column(String, nullable=False)  # TaskType enum as string
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)  # TaskCategory enum as string
    frequency = Column(String, nullable=False)  # TaskFrequency enum as string
    completed_at = Column(DateTime)
    schedule = Column(JSONB)  # TaskSchedule | None
    routine_id = Column(PGUUID)
    tags = Column(JSONB)  # list[TaskTag]
    actions = Column(JSONB)  # list[Action]

    __table_args__ = (
        Index("idx_tasks_date", "date"),
        Index("idx_tasks_routine_id", "routine_id"),
        Index("idx_tasks_user_id", "user_id"),
    )
