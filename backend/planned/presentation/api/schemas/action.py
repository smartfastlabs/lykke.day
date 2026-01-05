"""Action schema."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from planned.domain.value_objects.action import ActionType

from .base import BaseEntitySchema


class ActionSchema(BaseEntitySchema):
    """API schema for Action value object."""

    type: ActionType
    data: dict[str, str] = Field(default_factory=dict)
    created_at: datetime

