"""Schemas for early access endpoints."""

from pydantic import EmailStr, field_validator

from .base import BaseSchema


class EarlyAccessRequestSchema(BaseSchema):
    """Request body for early access opt-in."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def email_not_empty(cls, value: EmailStr) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("email is required")
        return cleaned.lower()


class StatusResponseSchema(BaseSchema):
    """Simple OK response."""

    ok: bool = True
