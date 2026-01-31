"""Schemas for SMS auth endpoints."""

from pydantic import field_validator

from lykke.core.utils.phone_numbers import normalize_phone_number

from .base import BaseSchema


class RequestSmsCodeSchema(BaseSchema):
    """Request body for requesting an SMS login code."""

    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("phone_number is required")
        normalized = normalize_phone_number(cleaned)
        if not normalized:
            raise ValueError("Invalid phone number")
        return normalized


class VerifySmsCodeSchema(BaseSchema):
    """Request body for verifying an SMS login code."""

    phone_number: str
    code: str

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("phone_number is required")
        normalized = normalize_phone_number(cleaned)
        if not normalized:
            raise ValueError("Invalid phone number")
        return normalized

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("code is required")
        if not cleaned.isdigit():
            raise ValueError("code must be digits only")
        return cleaned
