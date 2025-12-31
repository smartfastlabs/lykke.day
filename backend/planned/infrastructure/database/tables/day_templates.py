"""Day templates table definition."""

from sqlalchemy import Column, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class DayTemplate(Base):
    """Day template table for storing reusable day templates."""

    __tablename__ = "day_templates"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    slug = Column(String, nullable=False)
    alarm = Column(JSONB)  # Alarm | None
    icon = Column(String)

    __table_args__ = (
        Index("idx_day_templates_user_id", "user_id"),
        Index("idx_day_templates_user_slug", "user_id", "slug", unique=True),
    )

