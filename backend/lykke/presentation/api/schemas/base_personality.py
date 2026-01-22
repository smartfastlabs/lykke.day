"""Schemas for base personalities."""

from .base import BaseSchema


class BasePersonalitySchema(BaseSchema):
    """Schema for base personality metadata."""

    slug: str
    label: str
