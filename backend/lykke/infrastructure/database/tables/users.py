"""Users table definition."""

import uuid

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

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
    email: Mapped[str] = mapped_column(
        String(length=320), unique=True, index=True, nullable=True
    )
    phone_number = Column(String, nullable=True, unique=True)
    settings = Column(JSONB)  # UserSetting as JSONB
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="active")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
