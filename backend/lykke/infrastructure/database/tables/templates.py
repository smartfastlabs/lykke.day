"""Templates table definition."""

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class Template(Base):
    """Template table for storing user overrides."""

    __tablename__ = "templates"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    usecase = Column(String, nullable=False)
    key = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_templates_user_usecase_key", "user_id", "usecase", "key", unique=True),
    )
