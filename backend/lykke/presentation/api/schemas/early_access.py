"""Schemas for early access endpoints."""

from pydantic import EmailStr, field_validator, model_validator

from lykke.core.utils.phone_numbers import normalize_phone_number

from .base import BaseSchema


class EarlyAccessRequestSchema(BaseSchema):
    """Request body for early access opt-in."""

    email: EmailStr | None = None
    phone_number: str | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        return cleaned.lower()

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        return normalize_phone_number(cleaned)

    @model_validator(mode="after")
    def require_contact(self) -> "EarlyAccessRequestSchema":
        if not self.email and not self.phone_number:
            raise ValueError("email or phone_number is required")
        return self


class StatusResponseSchema(BaseSchema):
    """Simple OK response."""

    ok: bool = True
