"""Brain dump item schema."""

from datetime import datetime

from lykke.domain.value_objects.day import BrainDumpItemStatus

from .base import BaseEntitySchema


class BrainDumpItemSchema(BaseEntitySchema):
    """API schema for BrainDumpItem value object."""

    text: str
    status: BrainDumpItemStatus
    created_at: datetime | None = None
