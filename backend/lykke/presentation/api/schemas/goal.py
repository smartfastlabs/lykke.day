"""Goal schema."""

from datetime import datetime
from uuid import UUID

from lykke.domain.value_objects.day import GoalStatus

from .base import BaseEntitySchema


class GoalSchema(BaseEntitySchema):
    """API schema for Goal value object."""

    name: str
    status: GoalStatus
    created_at: datetime | None = None
