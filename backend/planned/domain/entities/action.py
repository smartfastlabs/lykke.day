from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from .. import value_objects
from .base import BaseConfigObject


class Action(BaseConfigObject):
    type: value_objects.ActionType
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
