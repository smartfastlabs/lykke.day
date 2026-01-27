"""Brain dump item schema."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from lykke.domain.value_objects.day import BrainDumpItemStatus, BrainDumpItemType

from .base import BaseEntitySchema, BaseSchema


class BrainDumpItemSchema(BaseEntitySchema):
    """API schema for BrainDump entity."""

    user_id: UUID
    date: date
    text: str
    status: BrainDumpItemStatus
    type: BrainDumpItemType
    created_at: datetime | None = None
    llm_run_result: dict[str, Any] | None = None


class BrainDumpSchema(BrainDumpItemSchema):
    """Alias schema for BrainDumpEntity."""


class BrainDumpItemCreateSchema(BaseSchema):
    """API schema for creating brain dump items."""

    date: date
    text: str


class BrainDumpItemUpdateSchema(BaseSchema):
    """API schema for updating a brain dump item."""

    status: BrainDumpItemStatus | None = None
    type: BrainDumpItemType | None = None
