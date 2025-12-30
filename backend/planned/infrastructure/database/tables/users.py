"""Users table definition."""

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class User(Base):
    """User table for storing user accounts."""

    __tablename__ = "users"

    uuid = Column(PGUUID, primary_key=True)
    email = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    password_hash = Column(Text, nullable=False)
    settings = Column(JSONB)  # UserSetting as JSONB
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("idx_users_email", "email", unique=True),)

