"""UseCase configs table definition."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class UseCaseConfig(Base):
    """UseCase config table for storing user-specific usecase configurations."""

    __tablename__ = "usecase_configs"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    usecase = Column(String, nullable=False)
    config = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index(
            "idx_usecase_configs_user_usecase",
            "user_id",
            "usecase",
            unique=True,
        ),
    )
