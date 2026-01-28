"""Brain dump schema."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from lykke.domain.value_objects.day import BrainDumpStatus, BrainDumpType

from .base import BaseEntitySchema, BaseSchema


class BrainDumpSchema(BaseEntitySchema):
    """API schema for BrainDump entity."""

    user_id: UUID
    date: date
    text: str
    status: BrainDumpStatus
    type: BrainDumpType
    created_at: datetime | None = None
    llm_run_result: dict[str, Any] | None = None


class BrainDumpCreateSchema(BaseSchema):
    """API schema for creating brain dumps."""

    date: date
    text: str


class BrainDumpUpdateSchema(BaseSchema):
    """API schema for updating a brain dump."""

    status: BrainDumpStatus | None = None
    type: BrainDumpType | None = None
