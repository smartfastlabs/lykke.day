"""Tasks table definition."""

from sqlalchemy import Column, Date, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class Task(Base):
    """Task table for storing scheduled tasks."""

    __tablename__ = "tasks"

    uuid = Column(PGUUID, primary_key=True)
    user_uuid = Column(PGUUID, nullable=False)
    date = Column(Date, nullable=False)  # extracted from scheduled_date for querying
    scheduled_date = Column(Date, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # TaskStatus enum as string
    task_definition = Column(JSONB, nullable=False)  # TaskDefinition
    category = Column(String, nullable=False)  # TaskCategory enum as string
    frequency = Column(String, nullable=False)  # TaskFrequency enum as string
    completed_at = Column(DateTime)
    schedule = Column(JSONB)  # TaskSchedule | None
    routine_uuid = Column(PGUUID)
    tags = Column(JSONB)  # list[TaskTag]
    actions = Column(JSONB)  # list[Action]

    __table_args__ = (
        Index("idx_tasks_date", "date"),
        Index("idx_tasks_routine_uuid", "routine_uuid"),
        Index("idx_tasks_user_uuid", "user_uuid"),
    )

