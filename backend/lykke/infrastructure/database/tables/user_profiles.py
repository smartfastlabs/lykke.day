"""User profiles table definition."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class UserProfile(Base):
    """Structured user profile table (1:1 with users)."""

    __tablename__ = "user_profiles"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)

    preferred_name = Column(String, nullable=True)
    goals = Column(JSONB, nullable=False, server_default="[]")  # list[str]
    work_hours = Column(JSONB, nullable=True)  # WorkHours VO as JSONB
    onboarding_completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_user_profiles_user_id", "user_id", unique=True),
    )

