"""Factoid schema."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from lykke.domain.value_objects.ai_chat import FactoidCriticality, FactoidType

from .base import BaseEntitySchema, BaseSchema


class FactoidCreateSchema(BaseSchema):
    """API schema for creating a Factoid entity."""

    content: str
    factoid_type: FactoidType = FactoidType.SEMANTIC
    criticality: FactoidCriticality = FactoidCriticality.NORMAL
    conversation_id: UUID | None = None
    ai_suggested: bool = False
    user_confirmed: bool = True


class FactoidUpdateSchema(BaseSchema):
    """API schema for Factoid update requests."""

    content: str | None = None
    factoid_type: FactoidType | None = None
    criticality: FactoidCriticality | None = None
    conversation_id: UUID | None = None
    user_confirmed: bool | None = None


class FactoidSchema(BaseEntitySchema):
    """Schema for Factoid entity."""

    user_id: UUID
    conversation_id: UUID | None = None
    factoid_type: str
    criticality: str
    content: str
    embedding: list[float] | None = None
    ai_suggested: bool = False
    user_confirmed: bool = False
    last_accessed: datetime
    access_count: int = 0
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
