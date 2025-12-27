from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import Field

from .base import BaseConfigObject


class ActionType(str, Enum):
    COMPLETE = "COMPLETE"
    DELETE = "DELETE"
    EDIT = "EDIT"
    NOTIFY = "NOTIFY"
    PAUSE = "PAUSE"
    PUNT = "PUNT"
    RESUME = "RESUME"
    START = "START"
    VIEW = "VIEW"


class Action(BaseConfigObject):
    type: ActionType
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
