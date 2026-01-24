"""DayTemplate schema."""

from datetime import time
from uuid import UUID

from pydantic import BaseModel, Field

from .base import BaseEntitySchema, BaseSchema
from .high_level_plan import HighLevelPlanSchema


class DayTemplateTimeBlockSchema(BaseModel):
    """API schema for a time block in a day template."""

    time_block_definition_id: UUID
    start_time: time
    end_time: time
    name: str


class DayTemplateCreateSchema(BaseSchema):
    """API schema for creating a DayTemplate entity."""

    slug: str
    start_time: time | None = None
    end_time: time | None = None
    icon: str | None = None
    routine_ids: list[UUID] = Field(default_factory=list)
    time_blocks: list[DayTemplateTimeBlockSchema] = Field(default_factory=list)
    high_level_plan: HighLevelPlanSchema | None = None


class DayTemplateSchema(DayTemplateCreateSchema, BaseEntitySchema):
    """API schema for DayTemplate entity."""

    user_id: UUID


class DayTemplateUpdateSchema(BaseSchema):
    """API schema for DayTemplate update requests."""

    slug: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    icon: str | None = None
    routine_ids: list[UUID] | None = None
    time_blocks: list[DayTemplateTimeBlockSchema] | None = None
    high_level_plan: HighLevelPlanSchema | None = None


class DayTemplateRoutineCreateSchema(BaseSchema):
    """API schema for attaching a routine to a day template."""

    routine_id: UUID


class DayTemplateTimeBlockCreateSchema(BaseSchema):
    """API schema for adding a time block to a day template."""

    time_block_definition_id: UUID
    start_time: time
    end_time: time
    # Note: name is not required in create request - it will be fetched from the TimeBlockDefinition
