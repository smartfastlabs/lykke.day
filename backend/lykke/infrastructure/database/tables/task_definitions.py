"""Task definitions table definition."""

from sqlalchemy import Column, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class TaskDefinition(Base):
    """Task definition table for storing reusable task templates."""

    __tablename__ = "task_definitions"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    type = Column(String, nullable=False)  # TaskType enum as string

    __table_args__ = (Index("idx_task_definitions_user_id", "user_id"),)
