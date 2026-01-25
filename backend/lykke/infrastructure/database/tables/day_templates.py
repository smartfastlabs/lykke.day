"""Day templates table definition."""

from sqlalchemy import Column, ForeignKey, Index, String, Text, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class DayTemplate(Base):
    """Day template table for storing reusable day templates."""

    __tablename__ = "day_templates"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    slug = Column(String, nullable=False)
    start_time = Column(Time)
    end_time = Column(Time)
    icon = Column(String)
    routine_definition_ids = Column(JSONB)  # list[UUID]
    time_blocks = Column(JSONB)  # list[DayTemplateTimeBlock]
    high_level_plan = Column(JSONB)  # HighLevelPlan | None

    __table_args__ = (
        Index("idx_day_templates_user_id", "user_id"),
        Index("idx_day_templates_user_slug", "user_id", "slug", unique=True),
    )
