"""Pydantic schemas for FastAPI Users."""

from uuid import UUID

from fastapi_users import schemas
from pydantic import field_validator

from lykke.core.utils.phone_numbers import normalize_phone_number


class UserRead(schemas.BaseUser[UUID]):
    """Schema for reading user data."""

    phone_number: str | None = None


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a new user."""

    phone_number: str

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone_number_input(cls, v: str | None) -> str:
        if v is None or not str(v).strip():
            msg = "Phone number is required"
            raise ValueError(msg)
        normalized = normalize_phone_number(str(v))
        if not normalized:
            msg = "Invalid phone number"
            raise ValueError(msg)
        return normalized


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating user data."""

    phone_number: str | None = None

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone_number_input(cls, v: str | None) -> str | None:
        if v is None:
            return None
        normalized = normalize_phone_number(v)
        return normalized or None
