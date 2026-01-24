"""API schemas for TimeBlockDefinition entities."""

from uuid import UUID

from lykke.domain import value_objects
from lykke.presentation.api.schemas.base import BaseEntitySchema, BaseSchema


class TimeBlockDefinitionCreateSchema(BaseSchema):
    """API schema for creating a TimeBlockDefinition."""

    name: str
    description: str
    type: value_objects.TimeBlockType
    category: value_objects.TimeBlockCategory


class TimeBlockDefinitionSchema(BaseEntitySchema):
    """API schema for TimeBlockDefinition entity."""

    user_id: UUID
    name: str
    description: str
    type: value_objects.TimeBlockType
    category: value_objects.TimeBlockCategory


class TimeBlockDefinitionUpdateSchema(BaseSchema):
    """API schema for TimeBlockDefinition update requests."""

    name: str | None = None
    description: str | None = None
    type: value_objects.TimeBlockType | None = None
    category: value_objects.TimeBlockCategory | None = None
