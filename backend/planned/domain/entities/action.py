from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from ..value_objects.action import ActionType
from .base import BaseConfigObject


class Action(BaseConfigObject):
    type: ActionType
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
