"""Users table definition."""

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User table for storing user accounts.

    Inherits from SQLAlchemyBaseUserTableUUID which provides:
    - id (UUID primary key)
    - email (unique, indexed)
    - hashed_password
    - is_active (default True)
    - is_superuser (default False)
    - is_verified (default False)
    """

    __tablename__ = "users"

    # Custom fields
    phone_number = Column(String, nullable=True)
    settings = Column(JSONB)  # UserSetting as JSONB
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

