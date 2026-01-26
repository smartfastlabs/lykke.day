"""API schemas for Trigger entities."""

from uuid import UUID

from lykke.presentation.api.schemas.base import BaseEntitySchema, BaseSchema


class TriggerCreateSchema(BaseSchema):
    """API schema for creating a Trigger."""

    name: str
    description: str


class TriggerSchema(TriggerCreateSchema, BaseEntitySchema):
    """API schema for Trigger entity."""

    user_id: UUID


class TriggerUpdateSchema(BaseSchema):
    """API schema for Trigger update requests."""

    name: str | None = None
    description: str | None = None


class TriggerTacticsUpdateSchema(BaseSchema):
    """API schema for updating tactics linked to a trigger."""

    tactic_ids: list[UUID]
