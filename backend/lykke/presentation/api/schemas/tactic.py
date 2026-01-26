"""API schemas for Tactic entities."""

from uuid import UUID

from lykke.presentation.api.schemas.base import BaseEntitySchema, BaseSchema


class TacticCreateSchema(BaseSchema):
    """API schema for creating a Tactic."""

    name: str
    description: str


class TacticSchema(TacticCreateSchema, BaseEntitySchema):
    """API schema for Tactic entity."""

    user_id: UUID


class TacticUpdateSchema(BaseSchema):
    """API schema for Tactic update requests."""

    name: str | None = None
    description: str | None = None
